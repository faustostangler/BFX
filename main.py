# beatforge/bfx.py

from beatforge.config import OUTPUT_DIR, PLAYLISTS
from typing import List, Dict
from beatforge import config
from beatforge.playlist import PlaylistManager
from beatforge.downloader import Downloader
from beatforge.bpm import BPMAnalyzer
from beatforge.converter import Converter
from beatforge.track import TrackDTO
import csv
import sqlite3
import os
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
                engagement_rate, title, artist, album, safe_title
            FROM track_info
        """):
            t = TrackDTO(
                url=row[0], view_count=row[1], like_count=row[2],
                comment_count=row[3], engagement_rate=row[4],
                title=row[5], artist=row[6], album=row[7], safe_title=row[8]
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
                'engagement_rate', 'title', 'artist', 'album', 'safe_title'
            ])
            for t in tracks:
                writer.writerow([
                    t.url, t.view_count, t.like_count, t.comment_count,
                    t.engagement_rate, t.title, t.artist, t.album, t.safe_title
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
                    engagement_rate, title, artist, album, safe_title
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.url, t.view_count, t.like_count, t.comment_count,
                t.engagement_rate, t.title, t.artist, t.album, t.safe_title
            ))
        conn.commit()
        conn.close()

    def _select_curated_tracks(self, tracks: List[TrackDTO]) -> List[TrackDTO]:
        """
        Retorna apenas os clássicos e novidades com base em views e engajamento.
        """
        classicos = self._group_by_views_and_engagement(tracks, 20, 10, bottom=False)
        novidades = self._group_by_views_and_engagement(tracks, 20, 10, bottom=True)
        return classicos + novidades

    def run(
        self,
        playlist_urls: List[str],
        process_all_entries: bool = True
    ) -> List[TrackDTO]:
        """
        Executa o pipeline em múltiplas playlists:
        1. Extrai e filtra faixas de cada playlist (todas ou curadas)
        2. Remove duplicatas globais por URL
        3. Executa o pipeline de processamento: download → BPM → MP3
        """
        all_tracks_by_url: Dict[str, TrackDTO] = {}

        for idx, url in enumerate(playlist_urls, 1):
            print(f"{idx}/{len(playlist_urls)} {url}")

            tracks = self.playlist_mgr.get_links(url, idx)

            selected_tracks = (
                tracks if process_all_entries else self._select_curated_tracks(tracks)
            )

            existing_tracks_by_url = self.load_tracks()
            for t in selected_tracks:
                if t.url not in existing_tracks_by_url:
                    all_tracks_by_url[t.url] = t  # sobrescreve se duplicado, mas ignora se já existe
            self.save_tracks(list(all_tracks_by_url.values()))

        unique_tracks = list(all_tracks_by_url.values())
        results: List[TrackDTO] = []
        self.save_tracks(unique_tracks)

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


                print(
                    f"{i+1}/{len(unique_tracks)} {raw_bpm:.2f} → {target_bpm} bpm {track.view_count} {track.engagement_rate:.2f} {track.safe_title}"
                )

            except Exception as e:
                print(f"✗ Erro em {track.safe_title}: {e}")

        return results
if __name__ == "__main__":
    runner = BeatForgeRunner(
        playlist_mgr=PlaylistManager(),
        downloader=Downloader(OUTPUT_DIR),
        analyzer=BPMAnalyzer(),
        converter=Converter(OUTPUT_DIR)
    )

    runner.run(PLAYLISTS)

    print("done!")
