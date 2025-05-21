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
from beatforge.spotify_bpm import SpotifyService, CSVRepository, BPMController

import argparse
import csv
import sqlite3
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
        Carrega faixas já salvas anteriormente, retornando um dicionário por URL.
        """
        db_path = f"{config.FILENAME}.db"
        tracks: Dict[str, TrackDTO] = {}

        if not os.path.exists(db_path):
            return tracks

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        for row in cur.execute("""
            SELECT url, view_count, like_count, comment_count,
                engagement_rate, engagement_score_alt, engagement_score_log,
                age_weight, title, artist, album, safe_title
            FROM track_info
        """):
            t = TrackDTO(
                url=row[0],
                view_count=row[1], like_count=row[2], comment_count=row[3],
                engagement_rate=row[4], engagement_score_alt=row[5],
                engagement_score_log=row[6], age_weight=row[7],
                title=row[8], artist=row[9], album=row[10], safe_title=row[11]
            )
            tracks[t.url] = t
        conn.close()
        return tracks

    def save_tracks(self, tracks: List[TrackDTO]) -> None:
        """
        Persiste as faixas únicas processadas em CSV e SQLite.
        """
        csv_path = f"{config.FILENAME}.csv"
        db_path = f"{config.FILENAME}.db"

        # CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'url', 'view_count', 'like_count', 'comment_count',
                'engagement_rate', 'engagement_score_alt', 'engagement_score_log',
                'age_weight', 'title', 'artist', 'album', 'safe_title'
            ])
            for t in tracks:
                writer.writerow([
                    t.url, t.view_count, t.like_count, t.comment_count,
                    t.engagement_rate, t.engagement_score_alt, t.engagement_score_log,
                    t.age_weight, t.title, t.artist, t.album, t.safe_title
                ])

        # SQLite
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
                CREATE TABLE IF NOT EXISTS track_info (
                    url TEXT PRIMARY KEY,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    engagement_rate REAL,
                    engagement_score_alt REAL,
                    engagement_score_log REAL,
                    age_weight INTEGER,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    safe_title TEXT
                )
        """)
        for t in tracks:
            cur.execute("""
                INSERT OR REPLACE INTO track_info (
                    url, view_count, like_count, comment_count,
                    engagement_rate, engagement_score_alt, engagement_score_log,
                    age_weight, title, artist, album, safe_title
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.url, t.view_count, t.like_count, t.comment_count,
                t.engagement_rate, t.engagement_score_alt, t.engagement_score_log,
                t.age_weight, t.title, t.artist, t.album, t.safe_title
            ))
        conn.commit()
        conn.close()

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
        max_tracks_per_playlist: int = config.MAX_TRACKS_PER_PLAYLIST
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
        for idx, url in enumerate(playlist_urls):
            extra_info=[f"{url}"]
            print_progress(idx, len(playlist_urls), start_time, extra_info, indent_level=0)

            tracks = self.playlist_mgr.get_links(url, idx, max_tracks_per_playlist)

            if process_all_entries:
                selected_tracks = tracks
            else:
                first = [tracks[0]]
                top_alt, top_log, top_viral = self._select_curated_tracks(tracks[1:], limit=5)

                seen = set()
                selected_tracks = []
                for t in first + top_alt + top_log + top_viral:
                    if t.url not in seen:
                        seen.add(t.url)
                        selected_tracks.append(t)

            for t in selected_tracks:
                if t.url not in existing_tracks_by_url:
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

                raw_bpm = self.analyzer.extract(wav_path)
                track.bpm = raw_bpm

                target_bpm = self.analyzer.choose_target(raw_bpm)
                track.target_bpm = target_bpm

                self.converter.convert(track)

                results.append(track)

                extra_info=[f"{raw_bpm:.2f} → {target_bpm} bpm {track.view_count} {track.engagement_rate:.2f} {track.safe_title}"]
                print_progress(i, len(unique_tracks), start_time, extra_info)

            except Exception as e:
                print(f"✗ Erro em {track.safe_title}: {e}")

        return results

def main():
    parser     = argparse.ArgumentParser(
        prog="beatforge",
        description="Processa playlists YouTube e/ou consulta Spotify"
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # ——— Modo “yt” ———
    yt = subparsers.add_parser(
        "yt",
        help="Faz download, análise e conversão das playlists definidas em playlist.txt"
    )
    yt.add_argument(
        "--with-spotify",
        action="store_true",
        help="Após o fluxo YouTube, enriquece cada TrackDTO com compasso/BPM do Spotify"
    )
    yt.add_argument(
        "--spotify-csv",
        default="",
        help="Se usar --with-spotify, salva resultados Spotify em CSV neste caminho"
    )

    # ——— Modo “spotify” ———
    sp = subparsers.add_parser(
        "spotify",
        help="Consulta compasso e BPM via Spotify API, sem baixar nada do YouTube"
    )
    sp.add_argument("--track",  required=True, help="Nome da música para busca")
    sp.add_argument("--artist", default="",   help="Nome do artista (opcional)")
    sp.add_argument("--csv",    default="",   help="Salvar resultados em CSV (opcional)")

    args = parser.parse_args()

    if args.mode == "yt":
        playlists_by_genre = load_playlists()
        start_time = time.time()
        all_track_dtos: list[TrackDTO] = []

        for i, (genre, urls) in enumerate(playlists_by_genre.items()):
            print(f"\n=== Processando gênero: {genre} ({len(urls)} playlists) ===")
            genre_dir = os.path.join(config.OUTPUT_DIR, genre)
            os.makedirs(genre_dir, exist_ok=True)

            runner = BeatForgeRunner(
                playlist_mgr=PlaylistManager(),
                downloader=Downloader(genre_dir),
                analyzer=BPMAnalyzer(),
                converter=Converter(genre_dir)
            )
            track_dtos = runner.run(
                urls,
                process_all_entries=False,
                max_tracks_per_playlist=config.MAX_TRACKS_PER_PLAYLIST
            )
            all_track_dtos.extend(track_dtos)
            print_progress(i,
                           len(playlists_by_genre),
                           start_time,
                           [f"{genre} concluído"])

        if args.with_spotify:
            # 1) prepare Spotify service & repo
            service    = SpotifyService(
                config.SPOTIPY_CLIENT_ID,
                config.SPOTIPY_CLIENT_SECRET
            )
            repo       = CSVRepository(args.spotify_csv) if args.spotify_csv else None
            controller = BPMController(service, repo)

            # 2) build (track_name, artist) queries
            queries = [(t.title, t.artist or "") for t in all_track_dtos]
            # 3) fetch TrackInfo from Spotify
            track_infos = controller.process(queries)

            # 4) map Spotify data back into your TrackDTOs
            for dto, info in zip(all_track_dtos, track_infos):
                dto.spotify_track_id = info.track_id
                dto.time_signature   = info.time_signature
                dto.spotify_bpm      = info.bpm

            # agora all_track_dtos está enriquecido e pronto para uso
        return

    if args.mode == "spotify":
        service    = SpotifyService(
            config.SPOTIPY_CLIENT_ID,
            config.SPOTIPY_CLIENT_SECRET
        )
        repo       = CSVRepository(args.csv) if args.csv else None
        controller = BPMController(service, repo)
        controller.process([(args.track, args.artist)])
        return

if __name__ == "__main__":
    main()

print('done!')