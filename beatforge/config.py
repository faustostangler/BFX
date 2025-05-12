import os

# Diretório de saída para arquivos WAV e MP3
OUTPUT_DIR = r"D:\Fausto Stangler\Videos\TubeDigger"

# Cria diretório se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Faixas de BPM e targets associados
MIN_BPM = 100
STEP = 20
MULTIPLIER = 2
MAX_BPM = MIN_BPM * MULTIPLIER

# Playlists do YouTube para processar
PLAYLISTS = [
    "https://www.youtube.com/watch?v=ELfzGV2Sa9w&list=PLJqUrQ44zEzVIX0spX2rICuTOZPwKUzyf",
    "https://www.youtube.com/watch?v=8muSkr1uJ00&list=PLJBUoC0dxcUwz0CyvP3uUHXB5LHANe-HG",
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&list=RD1vrEljMfXYo&start_radio=1",
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&playlist=RD1vrEljMfXYo&start_radio=1",
    "https://www.youtube.com/watch?v=1vrEljMfXYo&list=RD1vrEljMfXYo&start_radio=1&rv=1vrEljMfXYo",
    "https://www.youtube.com/watch?v=l0q7MLPo-u8&list=RDl0q7MLPo-u8&start_radio=1&rv=NAEppFUWLfc",
]
