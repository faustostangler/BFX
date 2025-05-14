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

# Playlists do YouTube para processar
PLAYLISTS = [
    "https://www.youtube.com/watch?v=WqawqSF4xs8&list=PLYvtHd8R6MRqrF49ofgC03FvIK_Q5cJaY&index=2",
    "https://www.youtube.com/watch?v=WqawqSF4xs8&list=RDWqawqSF4xs8&start_radio=1&rv=WqawqSF4xs8",
    "https://www.youtube.com/watch?v=7B4CLQGxHmI&list=PLtOGB4dki1N13w4bJIfDsUTWBSlJjnqqP&pp=8AUB",
    "https://www.youtube.com/watch?v=rPnXCPmrV3Y&list=RDrPnXCPmrV3Y&start_radio=1&rv=rPnXCPmrV3Y",
    "https://www.youtube.com/watch?v=XnqB4ZPQo1Q&list=RDXnqB4ZPQo1Q&start_radio=1&rv=XnqB4ZPQo1Q",
    "https://www.youtube.com/watch?v=UmRUp47SZ6s&list=RDUmRUp47SZ6s&start_radio=1&rv=UmRUp47SZ6s",
    "https://www.youtube.com/watch?v=a3Z4RWZa9WA&list=RDa3Z4RWZa9WA&start_radio=1&rv=a3Z4RWZa9WA",
    "https://www.youtube.com/watch?v=UYoATL_ymw8&list=RDUYoATL_ymw8&start_radio=1&rv=UYoATL_ymw8",
    "https://www.youtube.com/watch?v=3vCjvXpR1F0&list=RD3vCjvXpR1F0&start_radio=1&rv=3vCjvXpR1F0",
    "https://www.youtube.com/watch?v=lVXziMFEqX0&list=RDlVXziMFEqX0&start_radio=1&rv=lVXziMFEqX0",
    "https://www.youtube.com/watch?v=Rve03u7oEvI&list=RDRve03u7oEvI&start_radio=1&rv=Rve03u7oEvI",
    "https://www.youtube.com/watch?v=kOC30DBmK8A&list=RDkOC30DBmK8A&start_radio=1&rv=kOC30DBmK8A",
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
    "", 
]

MAX_TRACKS_PER_PLAYLIST = 100  # ou o valor desejado
