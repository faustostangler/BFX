import os
from pathlib import Path

# Injeção de dependência via ENV (Padrão 12-Factor)
OUTPUT_DIR = os.getenv("OUTPUT_DIR", str(Path.cwd() / "music"))
FILENAME = os.getenv("FILENAME", "playlist")
DATABASE_PATH = os.getenv("DATABASE_PATH", f"{FILENAME}.db")

# Cria diretório se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Faixas de BPM e targets associados
BPM_RANGE_START = 45
BPM_RANGE_END = 210
BPM_INTERVAL_SIZE = 20 # 20
BPM_TARGET_OFFSET = BPM_INTERVAL_SIZE * 3/4  # = 15
BPM_EXTREMES_MULTIPLIER = 2

MAX_TRACKS_PER_PLAYLIST = 25  # 25 ou o valor desejado
