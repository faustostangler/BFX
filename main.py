# beatforge/bfx.py

from beatforge.file_utils import load_playlists
from typing import List, Dict
from beatforge import config
from beatforge.playlist import PlaylistManager
from beatforge.downloader import Downloader
from beatforge.bpm import BPMAnalyzer
from beatforge.converter import Converter
from beatforge.track import TrackDTO
from beatforge.utils import print_progress
from beatforge.essentia_features import EssentiaFeatureExtractor
from beatforge.persistence import save_track_list, load_all_tracks, get_processed_urls

import csv
import sqlite3
import json
import os
import time
from typing import Tuple

class BeatForgeRunner:
    """
    Orquestrador principal do pipeline BeatForge:
    1. Carrega metadados de várias playlists
    2. Seleciona faixas com base em popularidade/engajamento
    3. Elimina duplicatas
    4. Executa pipeline: download → BPM → conversão
    """

    def __init__(
        self,
        playlist_mgr: PlaylistManager,
        downloader: Downloader,
        analyzer: BPMAnalyzer,
        converter: Converter
    ) -> None:
        self.playlist_mgr = playlist_mgr
        self.downloader   = downloader
        self.analyzer     = analyzer
        self.converter    = converter
        self.feature_extractor = EssentiaFeatureExtractor()

    @staticmethod
    def _select_first_and_top(
        tracks: List[TrackDTO],
        top_n: int, 
        top_n_views: int,
        top_n_eng: int,
        bottom: bool = False
    ) -> List[TrackDTO]:
        """
        Sempre mantém a primeira faixa da playlist (preservando ordem original)
        e seleciona as top_n seguintes com maior taxa de engajamento.

        Args:
            tracks: lista completa de TrackDTO de uma playlist.
            top_n: número de faixas adicionais após a primeira.
        Returns:
            Lista contendo até top_n+1 TrackDTO.
        """
        if not tracks:
            return []
        # Mantém o primeiro elemento intacto (primeiro vídeo)
        first = [tracks[0]]
        # Considera apenas o restante para ranking
        remainder = tracks[1:]

        sorted_tracks = sorted(
            remainder,
            key=lambda t: t.view_count or 0,
            reverse=not bottom
        )

        double_sorted_tracks = sorted(
            sorted_tracks[:top_n_views],
            key=lambda t: t.engagement_rate or 0.0,
            reverse=True
        )[:top_n_eng]

        return first + double_sorted_tracks

    @staticmethod
    def _group_by_views_and_engagement(
        tracks: List[TrackDTO],
        top_n_views: int,
        top_n_eng: int,
        bottom: bool = False
    ) -> List[TrackDTO]:
        """
        Seleciona faixas com base em views e taxa de engajamento.
        """
        sorted_by_views = sorted(
            tracks,
            key=lambda t: t.view_count or 0,
            reverse=not bottom
        )
        subset = sorted_by_views[:top_n_views]
        return sorted(
            subset,
            key=lambda t: t.engagement_rate or 0.0,
            reverse=True
        )[:top_n_eng]

    def load_tracks(self) -> Dict[str, TrackDTO]:
        """
        Loads all tracks from the database and returns them as a dictionary.

        Returns:
            Dict[str, TrackDTO]: A dictionary where the keys are track identifiers (str) and the values are TrackDTO objects representing each track.
        """
        db_path = f"{config.FILENAME}.db"
        return load_all_tracks(db_path)

    def save_tracks(self, tracks: List[TrackDTO]) -> None:
        save_track_list(tracks, f"{config.FILENAME}.db")

    def _select_curated_tracks(self, tracks: List[TrackDTO], limit: int) -> Tuple[List[TrackDTO], List[TrackDTO], List[TrackDTO]]:
        """
        Retorna três listas distintas:
        - top_alt: por engagement_score_alt (penalização linear)
        - top_log: por engagement_score_log (penalização logarítmica)
        - top_viral: por view_count (popularidade bruta)
        """
        # Top ALT
        filtered_alt = [t for t in tracks if t.engagement_score_alt is not None]
        top_alt = sorted(filtered_alt, key=lambda t: t.engagement_score_alt, reverse=True)[:limit]

        # Top LOG
        filtered_log = [t for t in tracks if t.engagement_score_log is not None]
        top_log = sorted(filtered_log, key=lambda t: t.engagement_score_log, reverse=True)[:limit]

        # Top VIRAL
        filtered_viral = [t for t in tracks if t.view_count is not None]
        top_viral = sorted(filtered_viral, key=lambda t: t.view_count, reverse=True)[:limit]

        return top_alt, top_log, top_viral

    def run(
        self,
        playlist_urls: List[str],
        process_all_entries: bool = True, 
        max_tracks_per_playlist: int = config.MAX_TRACKS_PER_PLAYLIST,
        processed: List[str] = []
    ) -> List[TrackDTO]:
        """
        Executa o pipeline em múltiplas playlists:
          1. Extrai metadados (PlaylistManager)
          2. Seleciona faixas (primeiro + top_n ou todas)
          3. Remove duplicatas globais
          4. Baixa áudio (Downloader)
          5. Extrai BPM (BPMAnalyzer)
          6. Converte para MP3 (Converter)

        Args:
            playlist_urls: URLs de playlists a processar.
            process_all_entries: se True, baixa todas as faixas; se False,
                baixa sempre o primeiro vídeo + TOP_TRACKS_PER_PLAYLIST.
        Returns:
            Lista de TrackDTO processados com wav_path e mp3_path preenchidos.
        """
        all_tracks_by_url: Dict[str, TrackDTO] = {}
        existing_tracks_by_url = self.load_tracks()

        print('\n\nGetting Youtube Info')
        start_time = time.time()
        for idx, playlist_url in enumerate(playlist_urls):
            extra_info=[f"{playlist_url}"]
            print_progress(idx, len(playlist_urls), start_time, extra_info, indent_level=0)

            tracks = self.playlist_mgr.get_links(playlist_url, idx, max_tracks_per_playlist, processed)

            if process_all_entries:
                selected_tracks = tracks
            else:
                first = [tracks[0]]
                top_alt, top_log, top_viral = self._select_curated_tracks(tracks[1:], limit=max_tracks_per_playlist)

                seen = set()
                selected_tracks = []
                for t in first + top_alt + top_log + top_viral:
                    if t.url not in seen:
                        seen.add(t.url)
                        selected_tracks.append(t)

            for t in selected_tracks[:max_tracks_per_playlist]:
                # if t.url not in existing_tracks_by_url:
                existing = existing_tracks_by_url.get(t.url)
                # só pular quem já tiver os dois BPMs preenchidos
                if existing and existing.bpm_librosa is not None and existing.bpm_essentia is not None:
                    continue
                all_tracks_by_url[t.url] = t  # sobrescreve se duplicado, mas ignora se já existe

        unique_tracks = list(all_tracks_by_url.values())
        results: List[TrackDTO] = []
        self.save_tracks(unique_tracks)

        print('\n\nDownloading Youtube Songs')
        start_time = time.time()
        for i, track in enumerate(unique_tracks):
            try:
                wav_path = self.downloader.download_to_wav(track.url, track.safe_title)
                track.wav_path = wav_path

                features = self.feature_extractor.extract_all(wav_path)
                track.bpm_essentia = features.get('bpm_essentia')
                track.tempo_confidence = features.get('tempo_confidence')
                track.beats_count = features.get('beats_count')
                track.onset_rate = features.get('onset_rate')
                track.harmonic_percussive_ratio = features.get('harmonic_percussive_ratio')
                track.key = features.get('key')
                track.scale = features.get('scale')
                track.key_strength = features.get('key_strength')
                track.timbral_mfcc_mean = features.get('timbral', {}).get('mfcc_mean')
                track.timbral_mfcc_std = features.get('timbral', {}).get('mfcc_std')
                track.spectral_centroid_avg = features.get('spectral', {}).get('centroid_avg')
                track.spectral_zcr_avg = features.get('spectral', {}).get('zcr_avg')
                track.spectral_rolloff_avg = features.get('spectral', {}).get('rolloff_avg')
                track.spectral_flatness_avg = features.get('spectral', {}).get('flatness_avg')
                track.spectral_flux_avg = features.get('spectral', {}).get('flux_avg')
                track.spectral_contrast_mean = features.get('spectral', {}).get('contrast_mean')
                track.spectral_dissonance_avg = features.get('spectral', {}).get('dissonance_avg')
                track.chroma_chroma_mean = features.get('chroma', {}).get('chroma_mean')
                track.chroma_chroma_std = features.get('chroma', {}).get('chroma_std')
                track.dynamics_energy_avg = features.get('dynamics', {}).get('energy_avg')
                track.dynamics_rms_avg = features.get('dynamics', {}).get('rms_avg')
                track.dynamics_loudness_avg = features.get('dynamics', {}).get('loudness_avg')
                track.dynamics_crest_factor = features.get('dynamics', {}).get('crest_factor')
                track.deep_embeds_vggish = features.get('deep_embeds', {}).get('vggish', [])

                bpm_librosa = self.analyzer.extract(wav_path)
                track.bpm_librosa = bpm_librosa

                target_bpm = self.analyzer.choose_target(track.bpm)
                track.target_bpm = target_bpm

                self.converter.convert(track)

                results.append(track)

                extra_info=[f"{track.bpm_essentia:.2f} → {target_bpm} bpm {track.view_count} {track.engagement_rate:.2f} {track.safe_title}"]
                print_progress(i, len(unique_tracks), start_time, extra_info)

            except Exception as e:
                print(f"✗ Erro em {track.safe_title}: {e}")

        self.save_tracks(unique_tracks)

        return results

if __name__ == "__main__":
    # 1) Carrega o dict { gênero: [urls...] }
    playlists_by_genre = load_playlists()
    db_path = f"{config.FILENAME}.db"
    processed = get_processed_urls(db_path)

    # 2) Para cada gênero, cria pasta e dispara o processamento
    start_time = time.time()
    items = playlists_by_genre.items()
    for i, (genre, urls) in enumerate(items):
        print(f"\n=== Processando gênero: {genre} ({len(urls)} playlists) ===")

        genre_dir = os.path.join(config.OUTPUT_DIR, genre)
        os.makedirs(genre_dir, exist_ok=True)

        runner = BeatForgeRunner(
            playlist_mgr=PlaylistManager(),
            downloader=Downloader(genre_dir),
            analyzer=BPMAnalyzer(),
            converter=Converter(genre_dir)
        )

        results = runner.run(urls, process_all_entries=False, max_tracks_per_playlist=config.MAX_TRACKS_PER_PLAYLIST, processed=processed)

        extra_info = [f"{genre} {len(results)} musics"]
        print_progress(i, len(items), start_time, extra_info)

print("done!")
pass