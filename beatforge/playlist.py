import csv
import sqlite3
from typing import List, Optional
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
from dataclasses import dataclass
import yt_dlp

@dataclass
class VideoInfo:
    """
    DTO que representa um vídeo do YouTube com estatísticas e metadados.
    """
    url: str
    view_count: int
    like_count: int
    comment_count: int
    engagement_rate: float
    title: str
    channel: str
    album: str

class PlaylistManager:
    """
    Gerencia extração de vídeos + estatísticas + metadados e persistência (CSV/SQLite).
    """

    def __init__(self) -> None:
        self._ydl_opts_flat = {
            'quiet': True,
            'extract_flat': True,
            'force_generic_extractor': False,
            'yes_playlist': True,
        }
        self._ydl_opts_full = {
            'quiet': True,
            'force_generic_extractor': False,
        }

    def sanitize_url(self, input_url: str) -> str:
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

    def fetch_entries(self, url: str) -> List[VideoInfo]:
        """
        1) Normaliza URL (playlist vs vídeo único)
        2) Extrai flat: só URLs/IDs
        3) Para cada URL, faz extração full pra pegar estatísticas + metadados
        4) Retorna lista de VideoInfo
        """
        clean_url = self.sanitize_url(url)

        # 1ª passagem: pegar IDs/URLs
        with yt_dlp.YoutubeDL(self._ydl_opts_flat) as ydl_flat:
            info = ydl_flat.extract_info(clean_url, download=False)

        entries = info.get('entries') or []
        urls = []
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
        video_infos: List[VideoInfo] = []

        # 2ª passagem: buscar metadata completo de cada vídeo
        with yt_dlp.YoutubeDL(self._ydl_opts_full) as ydl_full:
            total = len(unique_urls)
            for i, vid_url in enumerate(unique_urls, start=1):
                vid_info = ydl_full.extract_info(vid_url, download=False)
                vc = vid_info.get('view_count')   or 0
                lc = vid_info.get('like_count')   or 0
                cc = vid_info.get('comment_count') or 0
                er = (lc + cc) / vc if vc else 0

                title   = vid_info.get('title')   or ''
                channel = vid_info.get('uploader') or vid_info.get('channel') or ''
                album   = vid_info.get('album')   or ''

                # debug print opcional
                print(f"{vid_url} {i}/{total} {vc} {er:.02f} {title} - {channel} - {album}")

                video_infos.append(VideoInfo(
                    url=vid_url,
                    view_count=vc,
                    like_count=lc,
                    comment_count=cc,
                    engagement_rate=er,
                    title=title,
                    channel=channel,
                    album=album
                ))

        return video_infos

    def get_links(self, playlist_url: str, max_links: Optional[int] = None) -> List[VideoInfo]:
        infos = self.fetch_entries(playlist_url)
        self.save_infos_db(infos, 'playlist.db')
        infos_from_db = self.load_infos_db('playlist.db')

        return infos[:max_links] if max_links is not None else infos

    def save_infos_csv(self, infos: List[VideoInfo], csv_path: str) -> None:
        """Salva a lista de VideoInfo num arquivo CSV."""
        fieldnames = [
            'url', 'view_count', 'like_count', 'comment_count', 'engagement_rate',
            'title', 'channel', 'album'
        ]
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for v in infos:
                writer.writerow({
                    'url':             v.url,
                    'view_count':      v.view_count,
                    'like_count':      v.like_count,
                    'comment_count':   v.comment_count,
                    'engagement_rate': v.engagement_rate,
                    'title':           v.title,
                    'channel':         v.channel,
                    'album':           v.album,
                })

    def load_infos_csv(self, csv_path: str) -> List[VideoInfo]:
        """Carrega a lista de VideoInfo a partir de um CSV."""
        infos: List[VideoInfo] = []
        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                infos.append(VideoInfo(
                    url=row['url'],
                    view_count=int(row['view_count']),
                    like_count=int(row['like_count']),
                    comment_count=int(row['comment_count']),
                    engagement_rate=float(row['engagement_rate']),
                    title=row['title'],
                    channel=row['channel'],
                    album=row['album'],
                ))
        return infos

    def save_infos_db(self, infos: List[VideoInfo], db_path: str) -> None:
        """Salva a lista de VideoInfo em uma tabela SQLite."""
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS video_info (
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
        for v in infos:
            cur.execute("""
                INSERT OR REPLACE INTO video_info
                (url, view_count, like_count, comment_count, engagement_rate, title, channel, album)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                v.url, v.view_count, v.like_count, v.comment_count, v.engagement_rate,
                v.title, v.channel, v.album
            ))
        conn.commit()
        conn.close()

    def load_infos_db(self, db_path: str) -> List[VideoInfo]:
        """Carrega a lista de VideoInfo de uma tabela SQLite."""
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        infos: List[VideoInfo] = []
        for row in cur.execute("""
            SELECT url, view_count, like_count, comment_count,
                   engagement_rate, title, channel, album
            FROM video_info
        """):
            infos.append(VideoInfo(*row))
        conn.close()
        return infos
