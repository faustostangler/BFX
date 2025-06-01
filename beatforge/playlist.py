# beatforge/playlist.py

import csv
import sqlite3
import yt_dlp
import re
import time
import math
from datetime import datetime
import json

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
from typing import List, Optional, Dict, Any

from beatforge.track import TrackDTO
from beatforge import config
from beatforge.utils import print_progress
from beatforge.persistence import save_track_list

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

    def compute_engagement_scores(self, vc: int, lc: int, cc: int):
        """
        Calcula três métricas de engajamento a partir de views, likes e comentários:
        
        1. engagement_rate (er): medida tradicional baseada na soma de likes e comentários por view.
        Fórmula: (likes + comments) / views * 100_000

        2. score_alt: score de engajamento ajustado com penalização linear de visualizações.
        - Prioriza vídeos com alto engajamento relativo (comentários por view e por like),
            punindo diretamente vídeos muito populares.
        Fórmula: 0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * view_norm

        3. score_log: score semelhante ao alt, mas com penalização logarítmica de visualizações.
        - Mais permissivo com vídeos populares, desde que o engajamento proporcional seja alto.
        Fórmula: 0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * log(view_norm)

        - comment_rate      = comentários por view (escalado)
        - comment_to_like   = comentários por like (intensidade do engajamento)
        - view_norm         = penalização linear com base em 10M views como escala
        - view_log_norm     = penalização log(view_count) suaviza grandes audiências

        Retorna:
            (engagement_rate, engagement_score_alt, engagement_score_log)
        """
        if vc == 0:
            return 0.0, 0.0, 0.0

        multiplier = 10_000_000
        comment_rate = cc / vc * multiplier
        view_norm = vc / multiplier
        view_log_norm = math.log1p(vc) / math.log1p(multiplier)

        comment_to_like = cc / lc * (multiplier/100) if lc else 0.0

        score_alt = 0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * view_norm
        score_log = 0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * view_log_norm
        er = (multiplier/100) * (lc + cc) / vc

        return er, score_alt, score_log

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
        if not clean_url:
            return []
        
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
                try:
                    meta = ydl_full.extract_info(vid_url, download=False)
                except Exception:
                    continue

                ts = meta.get("timestamp") or 0
                age_days = 0
                if ts:
                    age_days = (datetime.now() - datetime.fromtimestamp(ts)).days
                    age_weight = math.log(age_days + 2) # +2 evita o log(0) e suaviza vídeos novíssimos


                vc = (meta.get('view_count') or 0)/age_weight
                lc = (meta.get('like_count') or 0)/age_weight
                cc = (meta.get('comment_count') or 0)/age_weight
                er, score_alt, score_log = self.compute_engagement_scores(vc, lc, cc)

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
                    engagement_score_alt=score_alt,
                    engagement_score_log=score_log,
                    title=title,
                    artist=artist,
                    album=album,
                    safe_title=safe_title, 
                    age_weight=age_weight, 
                ))

                extra_info = [f"{vid_url} ER={er:.2f} SCORE={score_log:.2f} V={vc:.0f} {title}"]
                print_progress(i, len(unique_urls), start_time, extra_info, indent_level=1)

        return tracks

    def get_links(self, playlist_url: str, idx: int, max_tracks_per_playlist: Optional[int] = None) -> List[TrackDTO]:
        all_tracks = self.fetch_entries(playlist_url, idx, max_tracks_per_playlist)

        # self.save_tracks_csv(all_tracks)
        save_track_list(all_tracks, f"{config.FILENAME}.db")

        return all_tracks[:max_tracks_per_playlist] if max_tracks_per_playlist is not None else all_tracks
