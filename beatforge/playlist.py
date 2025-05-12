# beatforge/playlist.py

import csv
import sqlite3
import yt_dlp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
from typing import List, Optional
from beatforge.track import TrackDTO

class PlaylistManager:
    """
    Gerencia a extração de vídeos e metadados do YouTube,
    retornando TrackDTO com estatísticas e metadados,
    além de suportar persistência em CSV e SQLite.
    """

    def __init__(self) -> None:
        """
        Inicializa o gerenciador com opções para extração "flat" (lista)
        e para extração completa (stats e metadados).
        """
        self._ydl_opts_flat = {
            'quiet': True,
            'extract_flat': True,         # só extrai IDs/URLs
            'force_generic_extractor': False,
            'yes_playlist': True,         # segue playlists/mixes
        }
        self._ydl_opts_full = {
            'quiet': True,
            'force_generic_extractor': False,
        }

    def sanitize_url(self, input_url: str) -> str:
        """
        Converte qualquer URL com 'list' ou 'playlist' num endpoint
        '/playlist?list=…', forçando o extractor de playlists do yt-dlp.
        Se não houver 'list' nem 'playlist', retorna a URL original.
        """
        parts = urlparse(input_url)
        qs = parse_qs(parts.query)
        list_id = (qs.get('list') or qs.get('playlist') or [None])[0]
        if list_id:
            return urlunparse((
                parts.scheme,
                parts.netloc,
                '/playlist',
                '',
                urlencode({'list': list_id}),
                ''
            ))
        return input_url

    def fetch_entries(self, url: str) -> List[TrackDTO]:
        """
        1) Normaliza a URL (playlist vs. vídeo único)
        2) Extrai “flat” para obter só IDs/URLs
        3) Monta lista de URLs únicas
        4) Para cada URL, faz extração completa para coletar:
           - view_count, like_count, comment_count
           - engagement_rate = (likes + comments) / views
           - title, channel, album
        5) Retorna: List[TrackDTO] já populado com esses metadados
        """
        clean_url = self.sanitize_url(url)

        # 1ª passagem: obter só os IDs/URLs
        with yt_dlp.YoutubeDL(self._ydl_opts_flat) as ydl_flat:
            info = ydl_flat.extract_info(clean_url, download=False)

        entries = info.get('entries') or []
        urls: List[str] = []
        if not entries:
            page = info.get('webpage_url') or f"https://www.youtube.com/watch?v={info['id']}"
            urls.append(page)
        else:
            for e in entries:
                vid = e.get('webpage_url') or e.get('url') or e.get('id')
                if not vid.startswith('http'):
                    vid = f"https://www.youtube.com/watch?v={vid}"
                urls.append(vid)

        unique_urls = list(OrderedDict.fromkeys(urls))

        # 2ª passagem: extrair estatísticas e metadados completos
        tracks: List[TrackDTO] = []
        with yt_dlp.YoutubeDL(self._ydl_opts_full) as ydl_full:
            total = len(unique_urls)
            for i, vid_url in enumerate(unique_urls, start=1):
                meta = ydl_full.extract_info(vid_url, download=False)
                vc = meta.get('view_count')   or 0
                lc = meta.get('like_count')   or 0
                cc = meta.get('comment_count') or 0
                er = (lc + cc) / vc if vc else 0

                title   = meta.get('title')    or ''
                channel = meta.get('uploader') or meta.get('channel') or ''
                album   = meta.get('album')    or ''

                # Debug opcional
                print(f"{vid_url} {i}/{total}  views={vc}  eng_rate={er:.2f}  "
                      f"'{title}' – {channel} – {album}")

                tracks.append(TrackDTO(
                    url=vid_url,
                    view_count=vc,
                    like_count=lc,
                    comment_count=cc,
                    engagement_rate=er,
                    title=title,
                    channel=channel,
                    album=album
                ))

        return tracks

    def get_links(self, playlist_url: str, max_links: Optional[int] = None) -> List[TrackDTO]:
        """
        Orquestra a extração de TrackDTOs:
          1) fetch_entries → lista completa de TrackDTO
          2) Aplica limite de max_links (se fornecido)
        """
        all_tracks = self.fetch_entries(playlist_url)
        self.save_tracks_csv(all_tracks, "playlist.csv")
        all_tracks = self.load_tracks_csv("playlist.csv")

        self.save_tracks_db(all_tracks, "playlist.db")
        tracks_from_db = self.load_tracks_db("playlist.db")

        return all_tracks[:max_links] if max_links is not None else all_tracks

    # ——— Persistência em CSV ————————————————————————————————————————
    def save_tracks_csv(self, tracks: List[TrackDTO], csv_path: str) -> None:
        """
        Salva a lista de TrackDTO num arquivo CSV.
        """
        fieldnames = [
            'url',
            'view_count',
            'like_count',
            'comment_count',
            'engagement_rate',
            'title',
            'channel',
            'album'
        ]
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for t in tracks:
                writer.writerow({
                    'url': t.url,
                    'view_count': t.view_count,
                    'like_count': t.like_count,
                    'comment_count': t.comment_count,
                    'engagement_rate': t.engagement_rate,
                    'title': t.title,
                    'channel': t.channel,
                    'album': t.album
                })

    def load_tracks_csv(self, csv_path: str) -> List[TrackDTO]:
        """
        Carrega a lista de TrackDTO a partir de um CSV.
        """
        tracks: List[TrackDTO] = []
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracks.append(TrackDTO(
                    url=row['url'],
                    view_count=int(row['view_count']),
                    like_count=int(row['like_count']),
                    comment_count=int(row['comment_count']),
                    engagement_rate=float(row['engagement_rate']),
                    title=row['title'],
                    channel=row['channel'],
                    album=row['album']
                ))
        return tracks

    # ——— Persistência em SQLite —————————————————————————————————————————
    def save_tracks_db(self, tracks: List[TrackDTO], db_path: str) -> None:
        """
        Salva a lista de TrackDTO em uma tabela SQLite.
        """
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
                channel TEXT,
                album TEXT
            )
        """)
        for t in tracks:
            cur.execute("""
                INSERT OR REPLACE INTO track_info
                (url, view_count, like_count, comment_count,
                 engagement_rate, title, channel, album)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                t.url,
                t.view_count,
                t.like_count,
                t.comment_count,
                t.engagement_rate,
                t.title,
                t.channel,
                t.album
            ))
        conn.commit()
        conn.close()

    def load_tracks_db(self, db_path: str) -> List[TrackDTO]:
        """
        Carrega a lista de TrackDTO de uma tabela SQLite.
        """
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tracks: List[TrackDTO] = []
        for row in cur.execute("""
            SELECT url, view_count, like_count, comment_count,
                   engagement_rate, title, channel, album
            FROM track_info
        """):
            tracks.append(TrackDTO(*row))
        conn.close()
        return tracks
