import librosa
from typing import List, Tuple
from beatforge import config
from essentia.standard import MonoLoader, RhythmExtractor2013


class BPMAnalyzer:
    """
    Serviço para análise de ritmo (BPM) em arquivos WAV
    e seleção de um BPM-alvo para conversão.

    A lógica segue parâmetros configuráveis definidos em config.py:
      - BPM_RANGE_START: BPM mínimo considerado
      - BPM_INTERVAL_SIZE: tamanho de cada faixa
      - BPM_TARGET_OFFSET: quanto somar ao início da faixa para obter o target
      - BPM_RANGE_END: BPM máximo antes de normalização
      - BPM_EXTREMES_MULTIPLIER: fator de correção para BPMs extremos
    """

    def __init__(self) -> None:
        """Gera dinamicamente as faixas de BPM com targets a partir de config.py"""
        self.min_bpm = config.BPM_RANGE_START
        self.max_bpm = config.BPM_RANGE_END
        self.interval = config.BPM_INTERVAL_SIZE
        self.offset = config.BPM_TARGET_OFFSET
        self.extreme_mult = config.BPM_EXTREMES_MULTIPLIER

        self.bpm_ranges = self._generate_ranges()

    def _generate_ranges(self) -> List[Tuple[float, float, int]]:
        """
        Gera faixas do tipo:
            (105, 125, 120)
            (125, 145, 140)
            ...
        Onde:
            - limite inferior = início da faixa
            - limite superior = início + intervalo
            - target = início + offset
        """
        ranges = []
        start = self.min_bpm
        while start < self.max_bpm:
            end = start + self.interval
            target = int(start + self.offset)
            # target = int(round(target / (self.interval/2)) * (self.interval/2))  # nearest-10 → 20
            ranges.append((start, end, target))
            start = end
        return ranges

    def extract(self, wav_path: str) -> float:
        """
        Extrai o BPM estimado a partir de um arquivo WAV.

        Fluxo:
          1. Carrega o .wav com librosa
          2. Estima o tempo (BPM)
          3. Normaliza extremos (<min ou >max)

        :param wav_path: Caminho absoluto do arquivo .wav
        :return: BPM ajustado (normalizado)
        """
        try:
            loader = MonoLoader(filename=wav_path, sampleRate=44100)
            audio = loader()
            rhythm = RhythmExtractor2013(method="multifeature")
            bpm, _, _, _, _ = rhythm(audio)  # Essentia retorna (bpm, beats, conf, ...)
            raw_bpm = float(bpm)
        except Exception:
            # --- 2) Fallback para Librosa (mantém compatibilidade) ---
            import librosa
            y, sr = librosa.load(wav_path, sr=None)
            tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
            raw_bpm = float(tempo if isinstance(tempo, (int, float)) else tempo[0])

        return self._normalize_bpm(raw_bpm)

    def choose_target(self, bpm: float) -> int:
        """
        Seleciona o BPM-alvo conforme as faixas geradas.
        Lança ValueError se o BPM não cair em nenhuma faixa.

        :param bpm: BPM já normalizado
        :return: target BPM da faixa correspondente
        """
        for low, high, target in self.bpm_ranges:
            if low <= bpm < high:
                return target
        raise ValueError(f"BPM fora do intervalo suportado: {bpm:.2f}")

    def _normalize_bpm(self, bpm: float) -> float:
        """
        Corrige BPMs extremos conforme fator definido:
          - bpm < min → bpm * fator
          - bpm > max → bpm / fator
          - caso contrário → mantém

        :param bpm: BPM bruto detectado
        :return: BPM normalizado
        """
        if bpm < self.min_bpm:
            return bpm * self.extreme_mult
        if bpm > self.max_bpm:
            return bpm / self.extreme_mult
        return bpm
