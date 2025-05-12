import librosa
from typing import List, Tuple


class BPMAnalyzer:
    """
    Serviço para análise de ritmo (BPM) em arquivos WAV
    e seleção de um BPM-alvo para conversão.
    """

    # Faixas: (limite_inferior, limite_superior, target_bpm)
    BPM_RANGES: List[Tuple[float, float, int]] = [
        (100, 125, 120),
        (125, 145, 140),
        (145, 165, 160),
        (165, 185, 180),
    ]

    def extract_bpm(self, wav_path: str) -> float:
        """
        Carrega WAV e estima o BPM pelo track de batidas do Librosa.
        Depois normaliza:
          - Se < 100: dobra
          - Se > 185: divide por 2
          - Caso contrário: mantém
        """
        y, sr = librosa.load(wav_path, sr=None)
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        raw_bpm = tempo if isinstance(tempo, (int, float)) else tempo[0]
        return self._normalize_bpm(float(raw_bpm))

    def choose_target(self, bpm: float) -> int:
        """
        Seleciona o BPM-alvo conforme faixas definidas.
        Lança ValueError se o BPM normalizado não cair em nenhuma faixa.
        """
        for low, high, target in self.BPM_RANGES:
            if low <= bpm < high:
                return target
        raise ValueError(f"BPM fora do intervalo suportado: {bpm:.2f}")

    def _normalize_bpm(self, bpm: float) -> float:
        """
        Normalização interna de BPM bruto:
          - bpm < 100 → bpm * 2
          - bpm > 185 → bpm / 2
          - caso contrário → bpm
        """
        if bpm < 100:
            return bpm * 2
        if bpm > 185:
            return bpm / 2
        return bpm
