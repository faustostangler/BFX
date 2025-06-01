import os
from pathlib import Path

# Diretório de saída para arquivos WAV e MP3
OUTPUT_DIR = r"D:\Fausto Stangler\Documentos\Python\BFX\music"
OUTPUT_DIR = str(Path.cwd() / "music")
FILENAME = "playlist"

# Cria diretório se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Faixas de BPM e targets associados
BPM_RANGE_START = 40
BPM_RANGE_END = 210
BPM_INTERVAL_SIZE = 20
BPM_TARGET_OFFSET = BPM_INTERVAL_SIZE * 3/4  # = 15
BPM_EXTREMES_MULTIPLIER = 2

MAX_TRACKS_PER_PLAYLIST = 3  # ou o valor desejado
