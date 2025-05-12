from beatforge.config import PLAYLISTS
from beatforge.downloader import Downloader
from beatforge.bpm import BPMAnalyzer
from beatforge.converter import Converter
import os
import time

class BeatForgeRunner:
    def __init__(self):
        self.downloader = Downloader()
        self.bpm_analyzer = BPMAnalyzer()
        self.converter = Converter()

    def process_playlist(self, playlist_url, max_links=20):
        print(playlist_url)
        links = self.downloader.get_playlist_links(playlist_url)
        print(f"Total de vídeos: {len(links)} → {min(max_links, len(links))}")
        self.process_links(links[:max_links])

    def process_links(self, links):
        for idx, link in enumerate(links, 1):
            print(idx, link)

            # 1) Obter título seguro e .wav
            try:
                title, wav_path = self.downloader.download_wav_with_title(link)
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ Falha no download: {e}")
                continue

            # 2) BPM
            try:
                bpm = self.bpm_analyzer.extract_and_normalize(wav_path)
                target = self.bpm_analyzer.choose_target_bpm(bpm)
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ BPM inválido: {e}")
                continue

            # 3) Converter se necessário
            try:
                self.converter.convert_if_needed(wav_path, title, bpm, target, idx)
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ Erro na conversão: {e}")

    def run(self):
        for url in PLAYLISTS:
            self.process_playlist(url)
        print("done!")

if __name__ == "__main__":
    runner = BeatForgeRunner()
    runner.run()


print('done!')