# beatforge/playlist.py

import yt_dlp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
from typing import List, Optional
from beatforge.track import TrackDTO

class PlaylistManager:
    """
    Gerencia a extração de vídeos e metadados do YouTube,
    retornando TrackDTO com estatísticas e metadados.
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
        return all_tracks[:max_links] if max_links is not None else all_tracks
