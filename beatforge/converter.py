# beatforge/modules/converter.py

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
        :param output_dir: diretório base para armazenar todos os MP3 convertidos.
        """
        self.base_dir = Path(output_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def convert(self, track: TrackDTO) -> Path:
        """
        Converte o WAV de uma TrackDTO para MP3 no BPM-alvo.

        Fluxo:
          1. Cria (se necessário) subpasta sob base_dir com nome do target BPM.
          2. Se o arquivo já existir, faz early return.
          3. Calcula multiplicador atempo = target_bpm / bpm.
          4. Chama ffmpeg para aplicar o filtro atempo.
          5. Atualiza track.mp3_path e retorna o Path.

        :param track: TrackDTO cujo .wav_path, .bpm e .target_bpm já estão preenchidos.
        :raises CalledProcessError: se o ffmpeg falhar.
        """
        out_dir = self.base_dir / str(track.target_bpm)
        out_dir.mkdir(exist_ok=True)

        out_mp3 = out_dir / f"{track.safe_title}_{track.target_bpm}bpm.mp3"

        # 2) Early return se já existe
        if out_mp3.exists():
            track.mp3_path = str(out_mp3)
            return out_mp3

        # 3) Cálculo do multiplicador de velocidade
        multiplier = round(track.target_bpm / track.bpm, 3)

        # 4) Execução do FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-i", track.wav_path,
            "-filter:a", f"atempo={multiplier}",
            "-vn",
            str(out_mp3)
        ]
        subprocess.run(cmd, check=True)

        # 5) Atualiza o DTO
        track.mp3_path = str(out_mp3)
        return out_mp3
