import os

# Diretório de saída para arquivos WAV e MP3
OUTPUT_DIR = r"D:\Fausto Stangler\Documentos\Python\BFX\Music"
FILENAME = "playlist"

# Cria diretório se não existir
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Faixas de BPM e targets associados
BPM_RANGE_START = 105
BPM_RANGE_END = 210
BPM_INTERVAL_SIZE = 20
BPM_TARGET_OFFSET = int(BPM_INTERVAL_SIZE * 3/4)  # = 15
BPM_EXTREMES_MULTIPLIER = 2

# Playlists do YouTube para processar
PLAYLISTS = [
    "https://www.youtube.com/watch?v=MBX2EDGX85o&list=RDGMEM29nh-so2GiiVvCzzeO3LJQ&start_radio=1&rv=g7MiWIUjY_U", 
    "https://www.youtube.com/watch?v=wNxNwvjzGM0&list=RDEMyQp0-Pw0tfsVei6KxE6K7g&start_radio=1&rv=w-kQaa4WPOs", 
    "https://www.youtube.com/watch?v=w1RTMZCTlaQ&list=RDGMEM29nh-so2GiiVvCzzeO3LJQ&start_radio=1&rv=a7JRyB1HKKI", 
    "https://www.youtube.com/watch?v=ELfzGV2Sa9w&list=PLJqUrQ44zEzVIX0spX2rICuTOZPwKUzyf",
    "https://www.youtube.com/watch?v=8muSkr1uJ00&list=PLJBUoC0dxcUwz0CyvP3uUHXB5LHANe-HG",
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&list=RD1vrEljMfXYo&start_radio=1",
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&playlist=RD1vrEljMfXYo&start_radio=1",
    "https://www.youtube.com/watch?v=1vrEljMfXYo&list=RD1vrEljMfXYo&start_radio=1&rv=1vrEljMfXYo",
    "https://www.youtube.com/watch?v=l0q7MLPo-u8&list=RDl0q7MLPo-u8&start_radio=1&rv=NAEppFUWLfc",
]
