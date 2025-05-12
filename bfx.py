from typing import List
from beatforge.config import PLAYLISTS
from beatforge.modules.playlist import PlaylistManager
from beatforge.modules.downloader import Downloader
from beatforge.modules.bpm import BPMAnalyzer
from beatforge.modules.converter import Converter
from beatforge.domain.track import TrackDTO


class BeatForgeRunner:
    """
    Controller principal do pipeline BeatForge.

    Responsabilidades:
      - Orquestrar o fluxo de dados entre módulos (Downloader, BPMAnalyzer, Converter).
      - Tratar exceções de alto nível e manter baixo acoplamento.
      - Expor interface simples para ‘run(playlist_url, max_tracks)’.
    """

    def __init__(
        self,
        playlist_mgr: PlaylistManager,
        downloader: Downloader,
        analyzer: BPMAnalyzer,
        converter: Converter
    ) -> None:
        """
        Injeta todas as dependências via composição, promovendo testabilidade e
        acoplamento fraco (Dependency Injection).
        """
        self.playlist_mgr = playlist_mgr
        self.downloader = downloader
        self.analyzer = analyzer
        self.converter = converter

    def run(self, playlist_url: str, max_tracks: int = 20) -> None:
        """
        Ponto de entrada do processamento:
          1. Obter lista de URLs via PlaylistManager.
          2. Para cada URL:
             a. Criar um TrackDTO (Data Transfer Object) vazio.
             b. Baixar WAV, extrair BPM, escolher target e converter para MP3.
        """
        try:
            urls = self.playlist_mgr.get_links(playlist_url, max_tracks)
            print(f"Total de faixas a processar: {len(urls)} (limitado a {max_tracks})")

            for idx, url in enumerate(urls, start=1):
                print(f"\n[{idx}/{len(urls)}] Processando: {url}")
                track = TrackDTO(url=url)

                # 1) Download do WAV
                track.wav_path = self.downloader.download_wav(track.url)

                # 2) Análise de BPM
                track.bpm = self.analyzer.extract_bpm(track.wav_path)

                # 3) Definição de target e conversão
                track.target_bpm = self.analyzer.choose_target(track.bpm)
                self.converter.convert(
                    wav_path=track.wav_path,
                    target_bpm=track.target_bpm,
                    safe_title=track.safe_title
                )

        except Exception as e:
            # Exceção genérica: registra e encerra graciosamente
            print(f"✗ Erro fatal: {e}")


if __name__ == "__main__":
    # Aqui estamos separando configuração (PLAYLISTS) da lógica de inicialização.
    runner = BeatForgeRunner(
        playlist_mgr=PlaylistManager(),
        downloader=Downloader(),
        analyzer=BPMAnalyzer(),
        converter=Converter()
    )

    # Exemplo de uso: iterar sobre várias playlists
    for url in PLAYLISTS:
        runner.run(url, max_tracks=20)

    print("✓ Pipeline concluído!")
