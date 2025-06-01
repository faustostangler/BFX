from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any

@dataclass
class TrackDTO:
    """
    Data Transfer Object que representa uma única faixa ao longo
    do pipeline BeatForge, incluindo metadados do YouTube.

    Atributos:
      - url: URL do vídeo YouTube a processar.
      - wav_path: caminho local para o .wav baixado.
      - bpm: valor de BPM extraído do arquivo .wav.
      - target_bpm: BPM alvo escolhido para a conversão.
      - mp3_path: caminho local para o .mp3 gerado.

      — Metadados do YouTube —
      - view_count: número de visualizações.
      - like_count: número de curtidas.
      - comment_count: número de comentários.
      - engagement_rate: (likes + comments) / views.
      - engagement_score_alt: score ponderado com penalização linear.
      - engagement_score_log: score ponderado com penalização log(view).
      - title: título do vídeo.
      - artist: nome do canal/uploader.
      - album: informação de álbum (se disponível).
    """
    url: str
    wav_path: Optional[str]     = field(default=None)
    bpm: Optional[float]        = field(default=None)
    target_bpm: Optional[int]   = field(default=None)
    mp3_path: Optional[str]     = field(default=None)

    # —— Metadados do YouTube ——
    age_weight: Optional[float]        = field(default=None)
    view_count: Optional[int]        = field(default=None)
    like_count: Optional[int]        = field(default=None)
    comment_count: Optional[int]     = field(default=None)
    engagement_rate: Optional[float] = field(default=None)
    engagement_score_alt: Optional[float] = field(default=None)
    engagement_score_log: Optional[float] = field(default=None)
    title: Optional[str]             = field(default=None)
    artist: Optional[str]            = field(default=None)
    album: Optional[str]             = field(default=None)
    safe_title: Optional[str]        = field(default=None)
    features: Dict[str, Any] | None  = field(default=None)

    def __repr__(self) -> str:
        """
        Mostra um resumo rápido: url, título e quantas keys há em features.
        Isso ajuda no debug, sem imprimir o dicionário inteiro.
        """
        num_feats = len(self.features or {})
        return f"<TrackDTO url={self.url!r}, title={self.title!r}, features_keys={num_feats}>"
