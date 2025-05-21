import yt_dlp
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from collections import OrderedDict
import os
import time
import glob
import re
import librosa
import subprocess


# 2) Faixas de target: (limite_inferior, limite_superior, target_bpm)
BPM_RANGES = [
    (100, 125, 120),
    (125, 145, 140),
    (145, 165, 160),
    (165, 185, 180),
]

playlists = [
    "https://www.youtube.com/watch?v=ELfzGV2Sa9w&list=PLJqUrQ44zEzVIX0spX2rICuTOZPwKUzyf", 
    "https://www.youtube.com/watch?v=8muSkr1uJ00&list=PLJBUoC0dxcUwz0CyvP3uUHXB5LHANe-HG", 
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&list=RD1vrEljMfXYo&start_radio=1", 
    "https://www.youtube.com/watch?v=FTQbiNvZqaY&playlist=RD1vrEljMfXYo&start_radio=1", 
    "https://www.youtube.com/watch?v=1vrEljMfXYo&list=RD1vrEljMfXYo&start_radio=1&rv=1vrEljMfXYo", 
    "https://www.youtube.com/watch?v=l0q7MLPo-u8&list=RDl0q7MLPo-u8&start_radio=1&rv=NAEppFUWLfc", 
]

# Configurações gerais
OUTPUT_DIR = r"D:\Fausto Stangler\Videos\TubeDigger"

os.makedirs(OUTPUT_DIR, exist_ok=True)
# # DIR_SUP = os.path.join(OUTPUT_DIR, f"{bpm_sup}")
# # DIR_INF = os.path.join(OUTPUT_DIR, f"{bpm_inf}")
# # os.makedirs(DIR_SUP, exist_ok=True)
# # os.makedirs(DIR_INF, exist_ok=True)
# DIR_SUP = OUTPUT_DIR
# DIR_INF = OUTPUT_DIR

class QuietLogger:
    def debug(self, *args, **kwargs): pass
    def warning(self, *args, **kwargs): pass
    def error(self, *args, **kwargs): pass

def safe_filename(name):
    name = name.replace(" ", "_")
    return re.sub(r'[^A-Za-z0-9_-]', "", name)[:128]

def cleanup_conflicts(base):
    for ext in ('webm','m4a','mp3','mp4'):
        path = os.path.join(OUTPUT_DIR, f"{base}.{ext}")
        if os.path.exists(path):
            try: os.remove(path)
            except: pass

def wait_for_file(path, timeout=60):
    start = time.time()
    while not os.path.exists(path):
        if time.time() - start > timeout:
            return False
        time.sleep(0.5)
    return True

def get_playlist_links(input_url):
    # 1) Sanitize mix URLs: keep only v & list params
    p       = urlparse(input_url)
    qs      = parse_qs(p.query)
    v       = qs.get('v', [None])[0]
    list_id = qs.get('list', [None])[0]

    if v and list_id and list_id.startswith('RD'):
        # rebuild as: https://www.youtube.com/watch?v=<v>&list=<RD...>
        new_qs = urlencode({'v': v, 'list': list_id})
        url = urlunparse((p.scheme, p.netloc, p.path, '', new_qs, ''))
    else:
        url = input_url

    # 2) Let yt-dlp handle both standard & mix playlists
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,         # just URLs, no metadata download
        'force_generic_extractor': False,
        'yes_playlist': True,         # API equivalent of --yes-playlist
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)

    # 3) Normalize to full watch-URLs and de-dupe
    entries = info.get('entries') or []
    links = []
    for e in entries:
        vid = e.get('url') or e.get('id')
        if not vid:
            continue
        if not vid.startswith('http'):
            vid = f"https://www.youtube.com/watch?v={vid}"
        links.append(vid)

    return list(OrderedDict.fromkeys(links))

def get_playlist_links_old(playlist_url):
    opts = {
        'quiet': True,
        'extract_flat': True,
        'force_generic_extractor': False,
    }
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(playlist_url, download=False)
        return [e['url'] for e in info.get('entries', []) if 'url' in e]

def download_to_wav(url, safe_title):
    wav_path = os.path.join(OUTPUT_DIR, f"{safe_title}.wav")
    if os.path.exists(wav_path):
        return wav_path

    cleanup_conflicts(safe_title)
    print(f"[{time.strftime('%H:%M:%S')}] iniciando download: {safe_title}")

    opts = {
        'format': 'bestaudio[abr<=128]',
        'outtmpl': os.path.join(OUTPUT_DIR, f"{safe_title}.%(ext)s"),
        'nopart': True,
        'continuedl': False,
        'quiet': True,
        'no_warnings': True,
        'restrictfilenames': True,
        'socket_timeout': 30,
        'retries': 3,
        'no_progress': True,
        'logger': QuietLogger(),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
            'preferredquality': '192',
        }],
    }

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

    if not wait_for_file(wav_path, timeout=60):
        raise TimeoutError(f"{wav_path} não apareceu em 60s")

    print(f"[{time.strftime('%H:%M:%S')}] WAV pronto: '{wav_path}'")
    return wav_path

def extract_bpm_librosa(wav_path):
    y, sr = librosa.load(wav_path, sr=None)
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    bpm = float(tempo if isinstance(tempo, (int, float)) else tempo[0])
    return round(bpm*2 if bpm < 100 else bpm, 2)

def compute_multiplier(original_bpm, target_bpm):
    return round(target_bpm / original_bpm, 3)

def normalize_bpm(bpm: float) -> float:
    """
    Ajusta BPM bruto:
     - Se < 100, dobra.
     - Se > 185, divide por 2.
     - Caso contrário, retorna inalterado.
    """
    if bpm < 100:
        return bpm * 2
    if bpm > 185:
        return bpm / 2
    return bpm

def choose_target(bpm: float) -> int:
    """
    Escolhe o target conforme as faixas definidas em BPM_RANGES.
    Lança ValueError se BPM não cair em nenhuma faixa.
    """
    for low, high, target in BPM_RANGES:
        if low <= bpm < high:
            return target
    raise ValueError(f"BPM fora do intervalo suportado: {bpm:.2f}")

def run_ffmpeg(wav_file, mult, out_mp3):
    cmd = [
        "ffmpeg", "-y",
        "-i", wav_file,
        "-filter:a", f"atempo={mult}",
        "-vn", out_mp3
    ]
    subprocess.run(cmd, check=True)
    return cmd

# # Obtém links da playlist
# query = parse_qs(urlparse(url).query)
# plist = query.get("list", [None])[0]
# playlist_url = f"https://www.youtube.com/playlist?list={plist}" if plist else url
# links = list(OrderedDict.fromkeys(get_playlist_links(playlist_url)))
# print(f"Total de vídeos na playlist: {len(links)}")

def get_mp3(links):
    # Processamento de cada link
    # for idx, link in enumerate(links[:20], 1):
    for idx, link in enumerate(links, 1):
        print(idx, link)
        # 1) metadata + safe_title
        with yt_dlp.YoutubeDL({'quiet':True,'no_warnings':True,'restrictfilenames':True}) as ydl_meta:
            info = ydl_meta.extract_info(link, download=False)
        safe_title = safe_filename(info['title'])
        wav_path   = os.path.join(OUTPUT_DIR, f"{safe_title}.wav")

        # 2) download WAV (com tratamento de WinError)
        try:
            wav_path = download_to_wav(link, safe_title)
        except Exception as e:
            if os.path.exists(wav_path):
                print(f"[{time.strftime('%H:%M:%S')}] ⚠ Warn: download error mas .wav existe, prosseguindo: {e}")
            else:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ Erro grave no download ({safe_title}): {e}")
                continue

        # 3) extrair e ajustar BPM
        try:
            bpm = extract_bpm_librosa(wav_path)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ Falha ao extrair BPM ({safe_title}): {e}")
            continue
        
        # escolhe target
        try:
            target = choose_target(bpm)
        except ValueError as ve:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ {ve} em {safe_title}")
            continue

        # 5) pular se já existir
        out_dir = os.path.join(OUTPUT_DIR, str(target))
        os.makedirs(out_dir, exist_ok=True)
        out_mp3 = os.path.join(out_dir, f"{safe_title}_{target}bpm.mp3")
        if os.path.exists(out_mp3):
            # print(f"[{time.strftime('%H:%M:%S')}] • Já existe: {safe_title}_{target}bpm.mp3 — pulando")
            continue

        # 6) converter com FFmpeg
        try:
            mult = compute_multiplier(bpm, target)
            run_ffmpeg(wav_path, mult, out_mp3)
            print(f"[{time.strftime('%H:%M:%S')}] ✓ {target} {idx}. {safe_title}: {bpm:.2f}→{target}bpm ({mult:.2f}x)")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] ✗ FFmpeg falhou em {safe_title} para {target}bpm: {e}")
            continue


for url in playlists:
    print(url)
    links = get_playlist_links(url)
    print(f"Total de vídeos: {len(links)}→20")
    get_mp3(links)

TOP_X = 20   # defina quantas “top” quer baixar

for url in playlists:
    links = get_playlist_links(url)
    if not links:
        continue

    primeira     = links[:1]
    top_x_musicas = links[1:TOP_X]
    to_download  = primeira + top_x_musicas

    print(f"Baixando 1ª  top {TOP_X} de {url}: total {len(to_download)} faixas")
    get_mp3(to_download)



print('done!')