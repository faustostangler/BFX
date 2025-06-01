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
        Carrega faixas já salvas anteriormente, retornando um dicionário por URL,
        agora incluindo o campo features (desserializado do JSON).
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
                   age_weight, title, artist, album, safe_title,
                   features_json
            FROM track_info
        """):
            # Desserializa o JSON de features
            raw_json = row[12]  # índice referente a features_json
            try:
                feats: Dict[str, Any] = json.loads(raw_json or "{}")
            except Exception:
                feats = {}

            t = TrackDTO(
                url=row[0],
                view_count=row[1],
                like_count=row[2],
                comment_count=row[3],
                engagement_rate=row[4],
                engagement_score_alt=row[5],
                engagement_score_log=row[6],
                age_weight=row[7],
                title=row[8],
                artist=row[9],
                album=row[10],
                safe_title=row[11],
                features=feats
            )
            tracks[t.url] = t
        conn.close()
        return tracks

    def save_tracks(self, tracks: List[TrackDTO]) -> None:
        """
        Persiste as faixas únicas processadas em CSV e SQLite.  
        Além dos metadados do YouTube, agora persistimos também o dicionário `features` (serializado JSON).

        Para o CSV, acrescentamos a coluna 'features_json'.  
        Para o SQLite, modificamos/criamos a tabela `track_info` acrescentando o campo `features_json TEXT`.
        """
        csv_path = f"{config.FILENAME}.csv"
        db_path = f"{config.FILENAME}.db"

        # ===== 1) CSV =====
        # Abrimos o CSV em modo 'w' (sobrescreve a cada execução).
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)

            # 1.1. Cabeçalho: adicionamos 'features_json' ao final.
            writer.writerow([
                'url', 'view_count', 'like_count', 'comment_count',
                'engagement_rate', 'engagement_score_alt', 'engagement_score_log',
                'age_weight', 'title', 'artist', 'album', 'safe_title',
                'features_json'
            ])

            # 1.2. Para cada TrackDTO: extraímos o dict features e convertemos para JSON string.
            for t in tracks:
                # Serializa o dicionário de features (ex: { "bpm": 115.9, "timbral": {...}, ... }) em uma string.
                features_str = json.dumps(t.features or {}, ensure_ascii=False)

                writer.writerow([
                    t.url,
                    t.view_count,
                    t.like_count,
                    t.comment_count,
                    t.engagement_rate,
                    t.engagement_score_alt,
                    t.engagement_score_log,
                    t.age_weight,
                    t.title,
                    t.artist,
                    t.album,
                    t.safe_title,
                    features_str
                ])

        # ===== 2) SQLite =====
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()

        # 2.1. Cria a tabela com todas as colunas (incluindo features_json) 
        #      caso ainda não exista.
        cur.execute("""
            CREATE TABLE IF NOT EXISTS track_info (
                url TEXT PRIMARY KEY,
                view_count INTEGER,
                like_count INTEGER,
                comment_count INTEGER,
                engagement_rate REAL,
                engagement_score_alt REAL,
                engagement_score_log REAL,
                age_weight REAL,
                title TEXT,
                artist TEXT,
                album TEXT,
                safe_title TEXT,
                features_json TEXT
            )
        """)
        conn.commit()

        # 2.2. Verifica se a coluna 'features_json' de fato está presente na tabela existente.
        #      Se não estiver, significa que esta tabela foi criada em execução anterior sem features_json.
        #      Nesse caso, dropamos a tabela inteira e recriamos com o esquema completo.
        cur.execute("PRAGMA table_info(track_info)")
        existing_columns = [row[1] for row in cur.fetchall()]  # row[1] = nome da coluna

        if "features_json" not in existing_columns:
            # Remove a tabela antiga (sem features_json) e cria de novo com o esquema correto
            cur.execute("DROP TABLE IF EXISTS track_info;")
            conn.commit()

            cur.execute("""
                CREATE TABLE track_info (
                    url TEXT PRIMARY KEY,
                    view_count INTEGER,
                    like_count INTEGER,
                    comment_count INTEGER,
                    engagement_rate REAL,
                    engagement_score_alt REAL,
                    engagement_score_log REAL,
                    age_weight REAL,
                    title TEXT,
                    artist TEXT,
                    album TEXT,
                    safe_title TEXT,
                    features_json TEXT
                )
            """)
            conn.commit()

        # 2.3. Agora que a tabela existe com features_json garantido, inserimos/atualizamos cada TrackDTO
        for t in tracks:
            features_str = json.dumps(t.features or {}, ensure_ascii=False)

            cur.execute("""
                INSERT OR REPLACE INTO track_info (
                    url, view_count, like_count, comment_count,
                    engagement_rate, engagement_score_alt, engagement_score_log,
                    age_weight, title, artist, album, safe_title,
                    features_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.url,
                t.view_count,
                t.like_count,
                t.comment_count,
                t.engagement_rate,
                t.engagement_score_alt,
                t.engagement_score_log,
                t.age_weight,
                t.title,
                t.artist,
                t.album,
                t.safe_title,
                features_str
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

                track.features = self.feature_extractor.extract_all(wav_path)

                json_path = os.path.splitext(wav_path)[0] + "_features.json"
                with open(json_path, "w", encoding="utf-8") as jf:
                    json.dump(track.features, jf, ensure_ascii=False, indent=2)

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

if __name__ == "__main__":
    # 1) Carrega o dict { gênero: [urls...] }
    playlists_by_genre = load_playlists()

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

        results = runner.run(urls, process_all_entries=False, max_tracks_per_playlist=config.MAX_TRACKS_PER_PLAYLIST)

        extra_info = [f"{genre} {len(results)} musics"]
        print_progress(i, len(items), start_time, extra_info)

print("done!")
