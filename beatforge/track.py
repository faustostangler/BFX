# beatforge/domain/track.py

from dataclasses import dataclass, field
from pathlib import Path
import re
from typing import Optional

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
      - title: título do vídeo.
      - channel: nome do canal/uploader.
      - album: informação de álbum (se disponível).
    """
    url: str
    wav_path: Optional[str]     = field(default=None)
    bpm: Optional[float]        = field(default=None)
    target_bpm: Optional[int]   = field(default=None)
    mp3_path: Optional[str]     = field(default=None)

    # —— Metadados do YouTube ——
    view_count: Optional[int]      = field(default=None)
    like_count: Optional[int]      = field(default=None)
    comment_count: Optional[int]   = field(default=None)
    engagement_rate: Optional[float] = field(default=None)
    title: Optional[str]           = field(default=None)
    channel: Optional[str]         = field(default=None)
    album: Optional[str]           = field(default=None)

    @property
    def safe_title(self) -> str:
        """
        Retorna um nome de arquivo “seguro” para usar em downloads:

        1. Se wav_path está disponível, usa seu stem (nome sem extensão).
        2. Caso contrário, extrai o parâmetro 'v' da URL como fallback.
        3. Substitui espaços por '_' e remove tudo que não for [A-Za-z0-9_-].
        4. Limita a 128 caracteres.
        """
        if self.wav_path:
            base = Path(self.wav_path).stem
        else:
            m = re.search(r"v=([^&]+)", self.url)
            base = m.group(1) if m else "track"

        # limpa caracteres inválidos
        cleaned = re.sub(r"[^A-Za-z0-9_-]", "", base.replace(" ", "_"))
        return cleaned[:128]
