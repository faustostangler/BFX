# beatforge/sampler.py

import subprocess
from pathlib import Path
from typing import Union

class Sampler:
    """
    Serviço para extrair um trecho (sample) de arquivos MP3.
    """

    def __init__(self, start_sec: int = 30, duration_sec: int = 15) -> None:
        """
        Inicializa o sampler com o tempo de início e duração desejados.
        """
        self.start_sec = start_sec
        self.duration_sec = duration_sec

    def create_sample(self, input_path: Union[str, Path]) -> Path:
        """
        Extrai o intervalo especificado e salva com o sufixo _sample.mp3
        na mesma pasta do arquivo original.
        """
        input_path = Path(input_path)
        if not input_path.exists():
            raise FileNotFoundError(f"Arquivo não encontrado: {input_path}")

        output_path = input_path.with_name(f"{input_path.stem}_sample.mp3")

        if output_path.exists():
            return output_path

        # Extrai o trecho usando ffmpeg
        # -ss: start time
        # -t: duration
        # -acodec copy: evita re-encoding se possível (rápido)
        cmd = [
            "ffmpeg", "-y",
            "-ss", str(self.start_sec),
            "-i", str(input_path),
            "-t", str(self.duration_sec),
            "-acodec", "libmp3lame",  # Forçando codec para garantir compatibilidade
            "-q:a", "2",              # Qualidade alta
            "-vn",
            str(output_path)
        ]

        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return output_path
