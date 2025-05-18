from dataclasses import dataclass
from typing import List, Optional, Tuple
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import csv
import logging

from beatforge import config

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TrackInfo:
    """DTO imutável com os dados retornados pela API Spotify."""
    track_id:       str
    name:           str
    artists:        List[str]
    time_signature: int
    bpm:            float


class InputValidator:
    """Validações de entrada para consulta."""
    @staticmethod
    def validate(name: str, artist: str) -> None:
        if not name.strip():
            raise ValueError("O nome da música não pode estar vazio.")


class SpotifyService:
    """Responsável por autenticar e buscar dados no Spotify."""
    def __init__(self, client_id: str, client_secret: str):
        creds = SpotifyClientCredentials(client_id=client_id,
                                         client_secret=client_secret)
        self.client = spotipy.Spotify(client_credentials_manager=creds)

    def search_track(self, name: str, artist: str = "") -> Optional[str]:
        query = f"track:{name}"
        if artist:
            query += f" artist:{artist}"
        resp = self.client.search(q=query, type="track", limit=1)
        items = resp.get("tracks", {}).get("items", [])
        if not items:
            return None
        return items[0]["id"]

    def get_audio_features(self, track_id: str) -> Optional[dict]:
        return self.client.audio_features([track_id])[0]


class CSVRepository:
    """Salva lista de TrackInfo em CSV."""
    def __init__(self, filepath: str):
        self.filepath = filepath

    def save(self, records: List[TrackInfo]) -> None:
        with open(self.filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Track ID", "Name", "Artists", "Time Signature", "BPM"])
            for t in records:
                writer.writerow([t.track_id, t.name, ";".join(t.artists), t.time_signature, t.bpm])
        logger.info(f"Salvo CSV em {self.filepath}")


class BPMController:
    """Orquestra consulta e saída (console e CSV opcional)."""
    def __init__(self,
                 service: SpotifyService,
                 repository: Optional[CSVRepository] = None):
        self.service    = service
        self.repository = repository

    def process(self, queries: List[Tuple[str, str]]) -> List[TrackInfo]:
        results: List[TrackInfo] = []
        for name, artist in queries:
            InputValidator.validate(name, artist)
            track_id = self.service.search_track(name, artist)
            if not track_id:
                logger.warning(f"Não encontrou: {name} — {artist}")
                continue

            feat = self.service.get_audio_features(track_id)
            if not feat:
                logger.warning(f"Sem audio_features: {track_id}")
                continue

            track = TrackInfo(
                track_id       = track_id,
                name           = feat.get("analysis_url", name),  # usa nome oficial se disponível
                artists        = [artist] if artist else [],
                time_signature = feat["time_signature"],
                bpm            = feat["tempo"]
            )
            print(f"Música: {track.name}")
            print(f"Artistas: {', '.join(track.artists) or '—'}")
            print(f"Compasso: {track.time_signature}/4")
            print(f"BPM: {track.bpm:.1f}")
            print("-" * 30)
            results.append(track)

        if self.repository and results:
            self.repository.save(results)

        return results


def main():
    import argparse
    from beatforge import config

    parser = argparse.ArgumentParser(
        description="Consulta BPM/Compasso no Spotify")
    parser.add_argument("--track",  required=True, help="Nome da música")
    parser.add_argument("--artist", default="",   help="Nome do artista (opcional)")
    parser.add_argument("--csv",    default="",   help="Salvar saída em CSV")
    args = parser.parse_args()

    service    = SpotifyService(config.SPOTIPY_CLIENT_ID,
                                config.SPOTIPY_CLIENT_SECRET)
    repo       = CSVRepository(args.csv) if args.csv else None
    controller = BPMController(service, repo)
    controller.process([(args.track, args.artist)])


if __name__ == "__main__":
    main()
