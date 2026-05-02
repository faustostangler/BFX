# beatforge/bfx.py

import os
from pathlib import Path
# Silenciar logs do TensorFlow e Essentia antes de importar o resto
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
try:
    import essentia
    essentia.log.infoActive = False
    essentia.log.warningActive = False
except ImportError:
    pass

from beatforge.file_utils import load_playlists
from typing import List, Dict
from beatforge import config
from beatforge.playlist import PlaylistManager
from beatforge.downloader import Downloader
from beatforge.bpm import BPMAnalyzer
from beatforge.converter import Converter
from beatforge.retargeter import Retargeter
from beatforge.sampler import Sampler
from beatforge.normalizer import Normalizer
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
import concurrent.futures
import threading

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
        converter: Converter,
        sampler: Sampler,
        retargeter: Retargeter,
        normalizer: Normalizer,
    ) -> None:
        self.playlist_mgr = playlist_mgr
        self.downloader   = downloader
        self.analyzer     = analyzer
        self.converter    = converter
        self.sampler      = sampler
        self.retargeter   = retargeter
        self.normalizer   = normalizer
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
        save_track_list(tracks, config.DATABASE_PATH)

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
        genre: str,
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
        print('\n\nGetting Youtube Info')
        def fetch_playlist_urls(idx: int, playlist_url: str):
            tracks = self.playlist_mgr.get_links(playlist_url, idx, max_tracks_per_playlist, list(processed))
            if not tracks:
                return []                     # se falhar, retorna vazio para não quebrar as outras
            
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

            return selected_tracks[:max_tracks_per_playlist]

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            playlist_futures = [executor.submit(fetch_playlist_urls, idx, url) for idx, url in enumerate(playlist_urls)]
            
            for future in concurrent.futures.as_completed(playlist_futures):
                selected_tracks = future.result()
                for t in selected_tracks:
                    existing = existing_tracks_by_url.get(t.url)
                    # só pular quem já tiver os dois BPMs preenchidos
                    if existing and existing.bpm_librosa is not None and existing.bpm_essentia is not None:
                        continue
                    all_tracks_by_url[t.url] = t  # sobrescreve se duplicado, mas ignora se já existe
                    t.genre = genre

        unique_tracks = list(all_tracks_by_url.values())
        results: List[TrackDTO] = []
        failed_tracks: List[TrackDTO] = []  # Lista para repescagem
        self.save_tracks(unique_tracks)

        print('\n\nDownloading Youtube Songs')
        start_time = time.time()
        
        print_lock = threading.Lock()
        completed_count = 0
        total_count = len(unique_tracks)

        def process_task(track: TrackDTO, is_retry: bool = False):
            nonlocal completed_count
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
                # intensidade bruta dos transientes. Como o cálculo de energia eleva as amplitudes ao quadrado, ele "exagera" matematicamente os picos curtos e fortes. O que significa na prática: Uma música com energy_avg altíssimo é uma música com batidas muito agressivas, tambores (bumbo, caixa) que "estouram" o sinal, mesmo que o resto da música seja baixo. É a "força bruta" dos picos do áudio.
                track.dynamics_rms_avg = features.get('dynamics', {}).get('rms_avg')
                # O RMS mede a potência contínua, o "corpo" do som. Se o RMS for muito alto (e próximo do limite máximo do áudio), significa que a música tem pouca dinâmica — ela é muito comprimida. É aquele som denso, contínuo, de um tijolo sonoro, comum em EDM (Música Eletrônica) ou Pop moderno, onde não há momentos de silêncio ou respiro.
                track.dynamics_loudness_avg = features.get('dynamics', {}).get('loudness_avg')
                # o volume "real" para o cérebro humano. Se você tocar duas músicas com o dial do volume travado no 5, a música com maior loudness_avg é aquela que vai fazer você querer tapar os ouvidos ou pedir para baixar, porque ela concentra a energia nas frequências que a biologia humana escuta melhor (a região dos médios, onde fica a voz, guitarras, etc.).
                track.dynamics_crest_factor = features.get('dynamics', {}).get('crest_factor')
                track.deep_embeds_vggish = features.get('deep_embeds', {}).get('vggish', [])

                # Relação Agressividade de Picos vs. Corpo: dynamics_energy_avg / dynamics_rms_avg: Relação Alta: A música tem picos brutais de volume, mas um "chão" sonoro (o corpo dos instrumentos) mais baixo e calmo. Isso indica alta dinâmica. Muito comum em Música Clássica, Jazz acústico, ou uma percussão muito seca e forte com silêncio em volta.
                # Relação Eficiência Perceptiva: dynamics_loudness_avg / dynamics_rms_avg: (Eficiência Perceptiva): Esta é a relação entre o que o seu ouvido percebe (Loudness) e o que o alto-falante está fisicamente gastando de energia elétrica (RMS). Relação baixa:: excesso de graves e sub-graves (muita energia e pouco barulho). Relação Alta: A música é extremamente eficiente para os ouvidos humanos. Ela soa muito alta para você, mesmo sem gastar tanta potência bruta do equipamento. Isso indica uma mixagem muito focada nas frequências médias/médio-agudas (2kHz a 5kHz - vozes bem na cara, guitarras brilhantes, metais). 
                # Relação Presença vs. Transientes: dynamics_loudness_avg / dynamics_energy_avg: Compara a presença humana (Loudness) contra a "violência" matemática dos picos (Energia). Relação Alta: A música é densa, clara e presente aos ouvidos, mas sem batidas pontiagudas ou agressivas. Pode indicar uma música ambiente de alta qualidade, um coral, sons de cordas contínuos (violinos), ou um pop muito suave e constante, onde a voz é o que mais brilha e a percussão é macia.

                bpm_librosa = self.analyzer.extract(wav_path)
                track.bpm_librosa = bpm_librosa

                target_bpm = self.analyzer.choose_target(track.bpm)
                track.target_bpm = target_bpm

                self.converter.convert(track)
                
                if track.mp3_path:
                    # Normalize in-place
                    self.normalizer.normalize(Path(track.mp3_path))
                    # Gera o sample de 15s (30-45s) do áudio normalizado
                    self.sampler.create_sample(track.mp3_path)

                # Retarget to global BPM (e.g. 160) se necessário
                if track.mp3_path and track.target_bpm:
                    self.retargeter.retarget(
                        mp3_path=Path(track.mp3_path),
                        source_bpm=track.target_bpm,
                        genre=track.genre or "Unknown"
                    )

                results.append(track)

                # Extrai o ID do worker e converte para 1-based se for dígito (ex: 0 -> W1)
                thread_name = threading.current_thread().name
                worker_id = thread_name.split('_')[-1].split('-')[-1]
                if worker_id.isdigit():
                    worker_id = str(int(worker_id) + 1)
                
                # Extrai apenas o ID do vídeo para o log
                vid_id = track.url.split('v=')[-1].split('&')[0] if 'v=' in track.url else track.url[-11:]
                extra_info=[f"{track.bpm_essentia:.2f}→{target_bpm}bpm V={track.view_count:.2f} ER={track.engagement_rate:.2f} https://youtu.be/{vid_id[:11]}"]
                with print_lock:
                    print_progress(completed_count, total_count, start_time, extra_info, worker_id=worker_id)
                    completed_count += 1

            except Exception as e:
                error_msg = str(e)
                if "confirm you're not a bot" in error_msg.lower() and not is_retry:
                    with print_lock:
                        print(f"\n[RETRY QUEUE] {track.safe_title} adicionado para repescagem (Bot detected)")
                    failed_tracks.append(track)
                else:
                    print(f"✗ Erro em {track.safe_title}: {e}")
                
                with print_lock:
                    completed_count += 1

        with concurrent.futures.ThreadPoolExecutor(max_workers=config.MAX_WORKERS) as executor:
            futures = [executor.submit(process_task, track) for track in unique_tracks]
            concurrent.futures.wait(futures)

        # === REPESCAGEM (Retry Logic) ===
        if failed_tracks:
            print(f"\n\n=== REPESCAGEM: Tentando {len(failed_tracks)} faixas que falharam por detecção de bot ===")
            # Na repescagem usamos max_workers=1 para evitar novos bloqueios por excesso de concorrência
            completed_count = 0
            total_count = len(failed_tracks)
            start_time_retry = time.time()
            
            for track in failed_tracks:
                process_task(track, is_retry=True)
                # O process_task já incrementa o completed_count e imprime o progresso
                # Mas como é sequencial, podemos imprimir algo extra se quiser.

        self.save_tracks(unique_tracks)

        return results

if __name__ == "__main__":
    # 1) Carrega o dict { gênero: [urls...] }
    playlists_by_genre = load_playlists()
    db_path = config.DATABASE_PATH
    processed = get_processed_urls(db_path)

    # Startup diagnostics
    if config.COOKIES_PATH:
        print(f"🍪 YouTube cookies loaded from: {config.COOKIES_PATH}")
    else:
        print("⚠ No cookies.txt found — YouTube may block some downloads")

    # 2) Para cada gênero, cria pasta e dispara o processamento
    start_time = time.time()
    items = playlists_by_genre.items()
    for i, (genre, urls) in enumerate(items):
        print(f"\n=== Processando gênero: {genre} ({len(urls)} playlists) ===")

        # Pasta temporária para os downloads de áudio bruto (.wav)
        temp_dl_dir = os.path.join(config.OUTPUT_DIR, "_downloads")

        sampler = Sampler()
        normalizer = Normalizer(
            target_lufs=config.LOUDNORM_TARGET_LUFS,
            true_peak=config.LOUDNORM_TRUE_PEAK,
            lra=config.LOUDNORM_LRA
        )
        runner = BeatForgeRunner(
            playlist_mgr=PlaylistManager(),
            downloader=Downloader(temp_dl_dir),
            analyzer=BPMAnalyzer(),
            converter=Converter(config.OUTPUT_DIR),
            sampler=sampler,
            retargeter=Retargeter(Path(config.OUTPUT_DIR), config.GLOBAL_TARGET_BPM, sampler),
            normalizer=normalizer,
        )

        results = runner.run(urls, genre=genre, process_all_entries=False, max_tracks_per_playlist=config.MAX_TRACKS_PER_PLAYLIST, processed=processed)

        extra_info = [f"{genre} {len(results)} musics"]
        print_progress(i, len(items), start_time, extra_info)

print("done!")
pass