from beatforge.config import OUTPUT_DIR, PLAYLISTS
from typing import List
from beatforge.playlist import PlaylistManager
from beatforge.downloader import Downloader
from beatforge.bpm import BPMAnalyzer
from beatforge.converter import Converter
from beatforge.track import TrackDTO


class BeatForgeRunner:
    """
    Controller principal do pipeline BeatForge.

    — Camada de Apresentação / Controller:
      Orquestra o fluxo entre serviços, mantendo baixo acoplamento
      (injeção de dependências via composição).

    — Responsabilidades:
      1. Obter links de playlist (PlaylistManager).
      2. Para cada link, criar um DTO (TrackDTO) e delegar a:
         - Downloader: baixar e extrair WAV.
         - BPMAnalyzer: extrair e normalizar BPM, escolher target.
         - Converter: gerar MP3 com FFmpeg.
      3. Tratar erros de alto nível sem interromper todo o pipeline.
      4. Retornar lista tipada de objetos de domínio (TrackDTO).
    """

    def __init__(
        self,
        playlist_mgr: PlaylistManager,
        downloader: Downloader,
        analyzer: BPMAnalyzer,
        converter: Converter
    ) -> None:
        """
        Injeção de dependências (Dependency Injection) reduz acoplamento
        e facilita testes unitários.

        — Composição em vez de herança quando possível.
        — Cada módulo encapsula sua própria lógica (separação de responsabilidades).
        """
        self.playlist_mgr = playlist_mgr
        self.downloader   = downloader
        self.analyzer     = analyzer
        self.converter    = converter

    def run(self, playlist_url: str, max_tracks: int = 20) -> List[TrackDTO]:
        """
        Interface pública: processa até `max_tracks` de uma playlist.

        Parâmetros:
            playlist_url (str): URL da playlist ou mix.
            max_tracks   (int): limite de faixas a processar.

        Retorna:
            List[TrackDTO]: lista de objetos de domínio com metadados
                            de cada faixa processada.
        """
        # 1) Obter URLs da playlist (camada de Service/Repository)
        urls = self.playlist_mgr.get_links(playlist_url)[:max_tracks]

        results: List[TrackDTO] = []
        for url in urls:
            track = TrackDTO(url=url)  # DTO: transporta dados entre camadas

            try:
                # 2) Download e extração de WAV
                wav_path = self.downloader.download_to_wav(track.url, track.safe_title)
                track.wav_path = wav_path

                # 3) Extração & normalização de BPM
                raw_bpm = self.analyzer.extract(wav_path)
                track.bpm = raw_bpm

                # 4) Escolha de target e conversão para MP3
                target_bpm = self.analyzer.choose_target(raw_bpm)
                track.target_bpm = target_bpm

                mp3_path = self.converter.convert(wav_path, raw_bpm, target_bpm)
                track.output_path = mp3_path

                results.append(track)
                print(f"✓ {track.safe_title}: {raw_bpm:.2f} → {target_bpm} bpm")
            except Exception as e:
                # Tratamento de erro de alto nível sem interromper o loop
                print(f"✗ Erro em {track.safe_title}: {e}")

        return results


if __name__ == "__main__":
    # **Composition Root**: montagem das dependências concretas
    runner = BeatForgeRunner(
        playlist_mgr=PlaylistManager(),
        downloader=Downloader(OUTPUT_DIR),
        analyzer=BPMAnalyzer(),
        converter=Converter(OUTPUT_DIR)
    )

    for pl_url in PLAYLISTS:
        runner.run(pl_url)
