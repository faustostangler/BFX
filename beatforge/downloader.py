# beatforge/downloader.py

import os
import time
from pathlib import Path
import yt_dlp


class Downloader:
    """Serviço de download e conversão de vídeos do YouTube para WAV."""

    def __init__(self, output_dir: str) -> None:
        """Inicializa o diretório de saída e cria a pasta se necessário."""
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def download_to_wav(self, url: str, safe_title: str) -> str:
        """
        Baixa o áudio de um vídeo do YouTube e o converte para WAV.

        Args:
            url (str): URL do vídeo YouTube.
            safe_title (str): Nome de arquivo já sanitizado.

        Returns:
            str: Caminho absoluto para o arquivo .wav gerado.

        Raises:
            TimeoutError: Se o arquivo .wav não for gerado dentro do tempo limite.
        """
        wav_path = os.path.join(self.output_dir, f"{safe_title}.wav")

        # Se o arquivo já existe, retorna direto
        if os.path.exists(wav_path):
            return wav_path

        # Limpa arquivos conflitantes antigos
        self._cleanup_conflicts(safe_title)

        # Configuração do yt-dlp
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

        # Baixa e converte com yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Aguarda até que o arquivo esteja disponível
        if not self._wait_for_file(wav_path):
            raise TimeoutError(f"{wav_path} não apareceu em 60 segundos")

        return wav_path

    def _cleanup_conflicts(self, base: str) -> None:
        """
        Remove arquivos com o mesmo nome base mas extensão diferente.

        Args:
            base (str): Nome base do arquivo (sem extensão).
        """
        for ext in ('webm', 'm4a', 'mp3', 'mp4'):
            path = os.path.join(self.output_dir, f"{base}.{ext}")
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    def _wait_for_file(self, path: str, timeout: int = 60) -> bool:
        """
        Aguarda até que o arquivo seja criado.

        Args:
            path (str): Caminho completo do arquivo a aguardar.
            timeout (int): Tempo máximo (segundos).

        Returns:
            bool: True se o arquivo apareceu, False se não.
        """
        start = time.time()
        while not os.path.exists(path):
            if time.time() - start > timeout:
                return False
            time.sleep(0.5)
        return True

    class _QuietLogger:
        """Logger silencioso usado pelo yt-dlp para suprimir mensagens."""
        def debug(self, *args, **kwargs): pass
        def warning(self, *args, **kwargs): pass
        def error(self, *args, **kwargs): pass
