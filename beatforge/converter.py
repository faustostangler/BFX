# beatforge/converter.py

import subprocess
from pathlib import Path
from typing import Union
from beatforge.track import TrackDTO


class Converter:
    """
    Serviço de conversão de arquivos WAV para MP3, ajustando a velocidade
    para atingir o BPM desejado.

    Responsabilidades:
      - Calcular o fator de atempo a partir de TrackDTO.bpm e TrackDTO.target_bpm.
      - Invocar o FFmpeg para gerar o MP3 na pasta adequada (<output_dir>/<target_bpm>/).
      - Atualizar TrackDTO.mp3_path com o caminho do arquivo gerado.
    """

    def __init__(self, output_dir: Union[str, Path]) -> None:
        """
        Inicializa o conversor com diretório base de saída.

        :param output_dir: diretório onde os arquivos convertidos serão salvos.
        """
        self.base_dir = Path(output_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def convert(self, track: TrackDTO) -> Path:
        """
        Converte o WAV de uma TrackDTO para MP3 com ajuste de tempo baseado em BPM.

        Fluxo:
          1. Cria subpasta com nome do target BPM.
          2. Se o arquivo já existe, retorna imediatamente.
          3. Calcula o multiplicador atempo (tempo relativo).
          4. Executa o FFmpeg com filtro de tempo.
          5. Atualiza track.mp3_path e retorna o caminho.

        :param track: TrackDTO com wav_path, bpm, target_bpm e safe_title definidos.
        :return: Caminho para o arquivo MP3 gerado.
        :raises subprocess.CalledProcessError: se o FFmpeg falhar.
        """
        out_dir = self.base_dir / str(track.target_bpm)
        out_dir.mkdir(exist_ok=True)

        out_mp3 = out_dir / f"{track.safe_title}_{track.target_bpm}bpm.mp3"

        if out_mp3.exists():
            track.mp3_path = str(out_mp3)
            return out_mp3

        multiplier = round(track.target_bpm / track.bpm, 3)

        cmd = [
            "ffmpeg", "-y",
            "-i", track.wav_path,
            "-filter:a", f"atempo={multiplier}",
            "-vn",
            str(out_mp3)
        ]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # apaga o WAV para liberar espaço em disco
        try:
            Path(track.wav_path).unlink(missing_ok=True)
        except Exception:
            pass

#         track.wav_path = None
        track.mp3_path = str(out_mp3)

        return out_mp3
