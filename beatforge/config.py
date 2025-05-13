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
    "https://www.youtube.com/watch?v=fRxDD4IBqBM&list=RDfRxDD4IBqBM&start_radio=1&rv=fRxDD4IBqBM",
    "https://www.youtube.com/watch?v=IFNntd48II8&list=RDEMaK28T3LQ4p-I9phy9DgvaQ&start_radio=1&rv=RVO3n6v-efI", 
    "https://www.youtube.com/watch?v=jUJP3B7xQO0&list=RDjUJP3B7xQO0&start_radio=1&rv=jUJP3B7xQO0", 
    "https://www.youtube.com/watch?v=SWjjdoCZCsw&list=RDSWjjdoCZCsw&start_radio=1&rv=SWjjdoCZCsw", 
    "https://www.youtube.com/watch?v=hmLBSCiEoas&list=RDhmLBSCiEoas&start_radio=1&rv=hmLBSCiEoas", 
    "https://www.youtube.com/watch?v=ooZR4LSuppk&list=RDEMGV0j-GSKjHvFNunei_eUbA&start_radio=1&rv=hmLBSCiEoas", 
    "https://www.youtube.com/playlist?list=PLtOGB4dki1N13w4bJIfDsUTWBSlJjnqqP", 
    "https://www.youtube.com/watch?v=qoA7Ise2fwQ&list=RDGMEM6ijAnFTG9nX1G-kbWBUCJA&start_radio=1&rv=gfiqW1WaGbw", 
    "https://www.youtube.com/watch?v=qoA7Ise2fwQ&list=RDqoA7Ise2fwQ&start_radio=1&rv=qoA7Ise2fwQ", 
    "https://www.youtube.com/watch?v=7qbEt_lSib4&list=RD7qbEt_lSib4&start_radio=1&rv=7qbEt_lSib4", 
    "https://www.youtube.com/watch?v=qmbx4_TQbkA&list=RDEMA-sxamFr763FjBY9H6dYig&start_radio=1&rv=7qbEt_lSib4", 
    "https://www.youtube.com/watch?v=N6eVx2iQRZ8&list=RDN6eVx2iQRZ8&start_radio=1&rv=N6eVx2iQRZ8", 
    "https://www.youtube.com/watch?v=-b0fwfhaak8&list=RD-b0fwfhaak8&start_radio=1&rv=-b0fwfhaak8", 
    # "", 
    # "", 
    # "", 
    # "", 
]

MAX_TRACKS_PER_PLAYLIST = 25  # ou o valor desejado
