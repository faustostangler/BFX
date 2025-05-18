import os

# Diretório de saída para arquivos WAV e MP3
OUTPUT_DIR = r"D:\Fausto Stangler\Documentos\Python\BFX\music"
FILENAME = "playlist"

# Cria diretório se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Faixas de BPM e targets associados
BPM_RANGE_START = 105
BPM_RANGE_END = 210
BPM_INTERVAL_SIZE = 10
BPM_TARGET_OFFSET = BPM_INTERVAL_SIZE * 3/4  # = 15
BPM_EXTREMES_MULTIPLIER = 2

MAX_TRACKS_PER_PLAYLIST = 15  # ou o valor desejado

SPOTIPY_CLIENT_ID     = os.getenv("SPOTIPY_CLIENT_ID", "119df1ec9b624c208852674d3492b3b6")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET", "fb505f1d6bca4decbc87691b192d613")
