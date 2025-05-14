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
    "https://www.youtube.com/watch?v=fF7VPXDJp4k&list=RDfF7VPXDJp4k&start_radio=1&rv=fF7VPXDJp4k",
    "https://www.youtube.com/watch?v=tGbRZ73NvlY&list=RDtGbRZ73NvlY&start_radio=1&rv=tGbRZ73NvlY",
    "https://www.youtube.com/watch?v=rtGSLV2sNKE&list=RDrtGSLV2sNKE&start_radio=1&rv=rtGSLV2sNKE",
    "https://www.youtube.com/watch?v=GufGgHMTMgU&list=RDGufGgHMTMgU&start_radio=1&rv=GufGgHMTMgU",
    "https://www.youtube.com/watch?v=E6COiEmuhWU&list=RDE6COiEmuhWU&start_radio=1&rv=E6COiEmuhWU",
    "https://www.youtube.com/watch?v=nX728deEGm0&list=RDnX728deEGm0&start_radio=1&rv=nX728deEGm0",
    "https://www.youtube.com/watch?v=WtsjrvwqIr0&list=RDWtsjrvwqIr0&start_radio=1&rv=WtsjrvwqIr0",
    "https://www.youtube.com/watch?v=Ek9Uyh_2Hmk&list=RDEk9Uyh_2Hmk&start_radio=1&rv=Ek9Uyh_2Hmk",
    "https://www.youtube.com/watch?v=OuiTHMuvqT4&list=RDOuiTHMuvqT4&start_radio=1&rv=OuiTHMuvqT4",
    "https://www.youtube.com/watch?v=lCMQ8HAXC-M&list=RDlCMQ8HAXC-M&start_radio=1&rv=lCMQ8HAXC-M",
    "https://www.youtube.com/watch?v=-FWmMVAxueU&list=RD-FWmMVAxueU&start_radio=1&rv=-FWmMVAxueU",
    "https://www.youtube.com/watch?v=Fc6izYdLhNE&list=RDFc6izYdLhNE&start_radio=1&rv=Fc6izYdLhNE",
    "https://www.youtube.com/watch?v=blUSVALW_Z4&list=RDblUSVALW_Z4&start_radio=1&rv=blUSVALW_Z4",
    "https://www.youtube.com/watch?v=gdYIpvnzoW8&list=RDgdYIpvnzoW8&start_radio=1&rv=gdYIpvnzoW8",
    "https://www.youtube.com/watch?v=7nsd0-5X5is&list=RD7nsd0-5X5is&start_radio=1&rv=7nsd0-5X5is",
    "https://www.youtube.com/watch?v=br-Ij3WMvsg&list=RDbr-Ij3WMvsg&start_radio=1&rv=br-Ij3WMvsg",
    "https://www.youtube.com/watch?v=t6omUxqhG78&list=RDt6omUxqhG78&start_radio=1&rv=t6omUxqhG78",
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

MAX_TRACKS_PER_PLAYLIST = 50  # ou o valor desejado
