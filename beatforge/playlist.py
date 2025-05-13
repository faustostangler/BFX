# beatforge/playlist.py

import csv
import sqlite3
import yt_dlp
import re
import time

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
from typing import List, Optional

from beatforge.track import TrackDTO
from beatforge import config
from beatforge.utils import print_progress

class PlaylistManager:
    """
    Gerencia a extração de vídeos e metadados do YouTube,
    retornando TrackDTO com estatísticas e metadados,
    além de suportar persistência em CSV e SQLite.
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

        # Se for uma playlist tipo RD... (mix automática), NÃO converte para /playlist
        if list_id and list_id.startswith("RD"):
            return input_url

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

    def make_safe_title(self, title: str, artist: str = "", album: str = "") -> str:
        def clean(s: str) -> str:
            return re.sub(r"[^A-Za-z0-9 \-]", "", s).strip().replace("  ", " ")

        title = clean(title)
        artist = clean(artist)
        album = clean(album)
        safe_title = f"{title} – {artist} – {album}".strip()
        return safe_title[:128]

    def fetch_entries(self, url: str, idx: int, max_tracks_per_playlist: int = config.MAX_TRACKS_PER_PLAYLIST) -> List[TrackDTO]:
        clean_url = self.sanitize_url(url)

        with yt_dlp.YoutubeDL(self._ydl_opts_flat) as ydl_flat:
            info = ydl_flat.extract_info(clean_url, download=False)

        if not info:
            print(f"✗ Nenhuma informação retornada para: {clean_url}")
            return []

        entries = info.get('entries') or []
        urls = []
        if not entries:
            page = info.get('webpage_url') or f"https://www.youtube.com/watch?v={info['id']}"
            urls.append(page)
        else:
            entries_max = entries[:max_tracks_per_playlist]
            for e in entries_max:
                vid = e.get('webpage_url') or e.get('url') or e.get('id')
                if not vid.startswith('http'):
                    vid = f"https://www.youtube.com/watch?v={vid}"
                urls.append(vid)

        unique_urls = list(OrderedDict.fromkeys(urls))

        tracks: List[TrackDTO] = []
        with yt_dlp.YoutubeDL(self._ydl_opts_full) as ydl_full:
            start_time = time.time()
            for i, vid_url in enumerate(unique_urls):
                meta = ydl_full.extract_info(vid_url, download=False)
                vc = meta.get('view_count') or 0
                lc = meta.get('like_count') or 0
                cc = meta.get('comment_count') or 0
                er = 100_000 * (lc + cc) / vc if vc else 0

                title = meta.get('title') or meta.get('fulltitle') or meta.get('alt_title') or meta.get('track') or ''
                artist = meta.get('artist') or meta.get('creator') or \
                         (meta.get('creators') or [None])[0] or \
                         meta.get('uploader') or meta.get('channel') or ''
                album = meta.get('album') or ''
                safe_title = self.make_safe_title(title, artist, album)

                tracks.append(TrackDTO(
                    url=vid_url,
                    view_count=vc,
                    like_count=lc,
                    comment_count=cc,
                    engagement_rate=er,
                    title=title,
                    artist=artist,
                    album=album,
                    safe_title=safe_title
                ))

                extra_info = [f"{vid_url} {vc} {er:.2f} {title} {artist}"]
                print_progress(i, len(unique_urls), start_time, extra_info, indent_level=1)

        return tracks

    def get_links(self, playlist_url: str, idx: int, max_links: Optional[int] = None) -> List[TrackDTO]:
        all_tracks = self.fetch_entries(playlist_url, idx)

        self.save_tracks_csv(all_tracks)
        self.save_tracks_db(all_tracks)

        return all_tracks[:max_links] if max_links is not None else all_tracks

    def save_tracks_csv(self, tracks: List[TrackDTO], csv_path: Optional[str] = None) -> None:
        if csv_path is None:
            csv_path = f"{config.FILENAME}.csv"

        fieldnames = [
            'url', 'view_count', 'like_count', 'comment_count',
            'engagement_rate', 'title', 'artist', 'album', 'safe_title'
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
                    'artist': t.artist,
                    'album': t.album,
                    'safe_title': t.safe_title
                })

    def load_tracks_csv(self, csv_path: Optional[str] = None) -> List[TrackDTO]:
        if csv_path is None:
            csv_path = f"{config.FILENAME}.csv"

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
                    artist=row['artist'],
                    album=row['album'],
                    safe_title=row['safe_title']
                ))
        return tracks

    def save_tracks_db(self, tracks: List[TrackDTO], db_path: Optional[str] = None) -> None:
        if db_path is None:
            db_path = f"{config.FILENAME}.db"

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

    def load_tracks_db(self, db_path: Optional[str] = None) -> List[TrackDTO]:
        if db_path is None:
            db_path = f"{config.FILENAME}.db"

        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        tracks: List[TrackDTO] = []
        for row in cur.execute("""
            SELECT url, view_count, like_count, comment_count,
                   engagement_rate, title, artist, album, safe_title
            FROM track_info
        """):
            tracks.append(TrackDTO(
                url=row[0], view_count=row[1], like_count=row[2],
                comment_count=row[3], engagement_rate=row[4],
                title=row[5], artist=row[6], album=row[7], safe_title=row[8]
            ))
        conn.close()
        return tracks
