from dataclasses import dataclass, field
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
      - engagement_score_alt: score ponderado com penalização linear.
      - engagement_score_log: score ponderado com penalização log(view).
      - title: título do vídeo.
      - artist: nome do canal/uploader.
      - album: informação de álbum (se disponível).
    """
    url: str
    wav_path: Optional[str]     = field(default=None)
    bpm_librosa: Optional[float]        = field(default=None)
    target_bpm: Optional[int]   = field(default=None)
    mp3_path: Optional[str]     = field(default=None)

    # —— Metadados do YouTube ——
    age_weight: Optional[float]            = field(default=None)
    view_count: Optional[int]              = field(default=None)
    like_count: Optional[int]              = field(default=None)
    comment_count: Optional[int]           = field(default=None)
    engagement_rate: Optional[float]       = field(default=None)
    engagement_score_alt: Optional[float]  = field(default=None)
    engagement_score_log: Optional[float]  = field(default=None)
    title: Optional[str]                   = field(default=None)
    artist: Optional[str]                  = field(default=None)
    album: Optional[str]                   = field(default=None)
    safe_title: Optional[str]              = field(default=None)

    # —— Atributos Essentia (achatados) ——
    bpm_essentia: Optional[float]                = field(default=None)
    tempo_confidence: Optional[float]            = field(default=None)
    beats_count: Optional[int]                   = field(default=None)
    onset_rate: Optional[float]                  = field(default=None)
    harmonic_percussive_ratio: Optional[float]   = field(default=None)
    key: Optional[int]                           = field(default=None)
    scale: Optional[int]                         = field(default=None)
    key_strength: Optional[float]                = field(default=None)

    timbral_mfcc_mean: Optional[float]           = field(default=None)
    timbral_mfcc_std: Optional[float]            = field(default=None)

    spectral_centroid_avg: Optional[float]       = field(default=None)
    spectral_zcr_avg: Optional[float]            = field(default=None)
    spectral_rolloff_avg: Optional[float]        = field(default=None)
    spectral_flatness_avg: Optional[float]       = field(default=None)
    spectral_flux_avg: Optional[float]           = field(default=None)
    spectral_contrast_mean: Optional[float]      = field(default=None)
    spectral_dissonance_avg: Optional[float]     = field(default=None)

    chroma_chroma_mean: Optional[float]          = field(default=None)
    chroma_chroma_std: Optional[float]           = field(default=None)

    dynamics_energy_avg: Optional[float]         = field(default=None)
    dynamics_rms_avg: Optional[float]            = field(default=None)
    dynamics_loudness_avg: Optional[float]       = field(default=None)
    dynamics_crest_factor: Optional[float]       = field(default=None)

    deep_embeds_vggish: list[float]              = field(default_factory=list)

    @property
    def bpm(self) -> Optional[float]:
        """
        Preferred BPM: use Essentia’s estimate if set,
        otherwise fall back to Librosa’s.
        """
        if self.bpm_essentia is not None:
            return self.bpm_essentia
        return self.bpm_librosa
