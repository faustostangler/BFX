import os
import time
from typing import Optional
import yt_dlp
from pathlib import Path


class Downloader:
    """
    Serviço de download de áudio de vídeos do YouTube e extração para WAV.

    Responsabilidades:
      - Baixar a melhor faixa de áudio até 128 kbps.
      - Converter para WAV via FFmpeg.
      - Gerenciar conflitos de nomes e aguardar geração do arquivo.
    """

    def __init__(self, output_dir: str) -> None:
        """
        :param output_dir: caminho onde todos os arquivos serão salvos.
        """
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def download_wav(self, url: str) -> str:
        """
        Baixa o áudio de um vídeo e retorna o caminho do .wav gerado.

        Fluxo:
          1. Obtém título do vídeo (sem download completo).
          2. Gera nome seguro e limpa arquivos antigos conflitantes.
          3. Chama yt-dlp com post-processor para WAV.
          4. Aguarda até o .wav existir (timeout 60 s).

        :param url: URL de um vídeo do YouTube.
        :return: caminho absoluto do arquivo WAV.
        :raises TimeoutError: se o arquivo não aparecer em 60 s.
        """
        title = self._get_title(url)
        safe_title = self._safe_filename(title)
        wav_path = os.path.join(self.output_dir, f"{safe_title}.wav")

        # Se já existe, evita novo download
        if os.path.exists(wav_path):
            return wav_path

        # Remove resquícios de downloads anteriores
        self._cleanup_conflicts(safe_title)

        # Configuração do yt-dlp para extrair áudio e converter
        ydl_opts = {
            'format': 'bestaudio[abr<=128]',
            'outtmpl': os.path.join(self.output_dir, f"{safe_title}.%(ext)s"),
            'nopart': True,
            'continuedl': False,
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
            'socket_timeout': 30,
            'retries': 3,
            'no_progress': True,
            'logger': self._QuietLogger(),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not self._wait_for_file(wav_path):
            raise TimeoutError(f"{wav_path} não apareceu em 60 segundos")

        return wav_path

    def _get_title(self, url: str) -> str:
        """
        Busca apenas o título do vídeo, sem baixar o arquivo.
        """
        opts = {
            'quiet': True,
            'no_warnings': True,
            'restrictfilenames': True,
        }
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        return info.get('title', 'track')

    class _QuietLogger:
        """Logger mudo para yt-dlp."""
        def debug(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass

    def _safe_filename(self, name: str) -> str:
        """
        Converte título em nome de arquivo seguro:
        - Espaços viram underscore
        - Remove caracteres não alfanuméricos, exceto - e _
        - Limita a 128 caracteres
        """
        tmp = name.replace(" ", "_")
        tmp = "".join(c for c in tmp if c.isalnum() or c in ("-", "_"))
        return tmp[:128]

    def _cleanup_conflicts(self, base: str) -> None:
        """
        Remove arquivos antigos que possam conflitar com o novo download.
        """
        for ext in ('webm', 'm4a', 'mp3', 'mp4'):
            path = os.path.join(self.output_dir, f"{base}.{ext}")
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def _wait_for_file(self, path: str, timeout: int = 60) -> bool:
        """
        Aguarda até o arquivo existir ou até expirar o timeout.
        """
        start = time.time()
        while not os.path.exists(path):
            if time.time() - start > timeout:
                return False
            time.sleep(0.5)
        return True
