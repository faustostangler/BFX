# beatforge/essentia_features.py

import numpy as np
import traceback

from essentia.standard import (
    MonoLoader,
    RhythmExtractor2013,
    FrameGenerator,
    Windowing,
    Spectrum,
    Centroid,
    ZeroCrossingRate,
    Energy,
    MFCC,
    RMS,
    Loudness,
    KeyExtractor,
    Onsets,
    Resample,
    MelBands
)

# Tentar importar algoritmos “opcionais”; se não existirem, definimos como None
try:
    from essentia.standard import Chromagram
except ImportError:
    Chromagram = None

try:
    from essentia.standard import HPCP
except ImportError:
    HPCP = None

try:
    from essentia.standard import HPSS
except ImportError:
    HPSS = None

try:
    from essentia.standard import SpectralRolloff
except ImportError:
    SpectralRolloff = None

try:
    from essentia.standard import SpectralFlatness
except ImportError:
    SpectralFlatness = None

try:
    from essentia.standard import SpectralFlux
except ImportError:
    SpectralFlux = None

try:
    from essentia.standard import SpectralContrast
except ImportError:
    SpectralContrast = None

try:
    from essentia.standard import Dissonance
except ImportError:
    Dissonance = None

try:
    from essentia.standard import Crest
except ImportError:
    Crest = None

# TensorflowPredict também pode não estar presente (depende da instalação do Essentia)
try:
    from essentia.standard import TensorflowPredict
except ImportError:
    TensorflowPredict = None


class EssentiaFeatureExtractor:
    """
    Extrator de múltiplas características musicais usando Essentia.
    Cada algoritmo opcional é utilizado somente se estiver disponível na versão instalada.
    """

    def __init__(self, frame_size=1024, hop_size=512):
        self.frame_size = frame_size
        self.hop_size = hop_size

        # ——— Componentes obrigatórios (sempre presentes) ———
        self.windowing = Windowing(type="hann")
        self.spectrum = Spectrum()

        # Timbre / MFCC
        self.mfcc = MFCC()

        # Atributos espectrais básicos
        self.centroid = Centroid()
        self.zcr = ZeroCrossingRate()

        # Dinâmica
        self.energy = Energy()
        self.rms = RMS()
        self.loudness = Loudness()

        # Key / Tonalidade
        self.key_extractor = KeyExtractor()

        # Onsets
        self.onsets = Onsets() if Onsets is not None else None

        # Resample e MelBands (sempre existem)
        self.resample16k = Resample(inputSampleRate=44100, outputSampleRate=16000)
        self.mel_bands_vgg = MelBands(
            numberBands=96,
            sampleRate=16000,
            fftSize=512,
            highFrequencyBound=8000
        )

        # ——— Componentes opcionais ———

        # Chromagram
        self.chromagram = (
            Chromagram(sampleRate=44100, frameSize=frame_size, hopSize=hop_size)
            if Chromagram is not None else None
        )

        # HPCP
        self.hpcp = HPCP(sampleRate=44100) if HPCP is not None else None

        # HPSS
        self.hpss = HPSS(filterSizes=[31, 31], sampleRate=44100) if HPSS is not None else None

        # SpectralRolloff, SpectralFlatness, SpectralFlux, SpectralContrast, Dissonance
        self.rolloff = SpectralRolloff(cutoff=0.85) if SpectralRolloff is not None else None
        self.flatness = SpectralFlatness() if SpectralFlatness is not None else None
        self.flux = SpectralFlux() if SpectralFlux is not None else None
        self.spectral_contrast = (
            SpectralContrast(sampleRate=44100, frameSize=frame_size, hopSize=hop_size)
            if SpectralContrast is not None else None
        )
        self.dissonance = Dissonance() if Dissonance is not None else None

        # Crest
        self.crest = Crest() if Crest is not None else None

        # TensorflowPredict (VGGish)
        if TensorflowPredict is not None:
            # Ajuste estes paths para onde você salvou os arquivos VGGish
            vggish_model_path = "/path/to/vggish_model.pb"
            vggish_meta_path = "/path/to/vggish_meta.json"
            try:
                self.tf_vggish = TensorflowPredict(
                    modelFilename=vggish_model_path,
                    jsonFilename=vggish_meta_path,
                    inputNodes=["vggish_input"],
                    outputNodes=["vggish_embedding"]
                )
            except Exception:
                self.tf_vggish = None
        else:
            self.tf_vggish = None

    def extract_all(self, wav_path: str) -> dict:
        """
        Extrai todas as features disponíveis de um arquivo WAV.
        Se um algoritmo não estiver presente na instalação, será ignorado.
        """
        try:
            audio = MonoLoader(filename=wav_path)()
            duration_secs = len(audio) / 44100.0

            # ——— Ritmo (BPM, confiança, contagem de beats) ———
            bpm = 0.0
            confidence = 0.0
            beats = []
            try:
                rhythmer = RhythmExtractor2013(method="multifeature")
                bpm, beats, confidence, _, _ = rhythmer(audio)
            except Exception:
                pass

            # ——— Onsets (taxa de onsets por segundo) ———
            onset_rate = 0.0
            if self.onsets is not None:
                try:
                    onset_times = self.onsets(audio)
                    onset_rate = len(onset_times) / duration_secs if duration_secs > 0 else 0.0
                except Exception:
                    onset_rate = 0.0

            # ——— HPSS (relação harmônica/percussiva) ———
            hp_ratio = 0.0
            if self.hpss is not None:
                try:
                    harmonic, percussive = self.hpss(audio)
                    harm_energy = self.energy(harmonic) if harmonic is not None else 0.0
                    perc_energy = self.energy(percussive) if percussive is not None else 0.0
                    hp_ratio = perc_energy / (harm_energy + 1e-9)
                except Exception:
                    hp_ratio = 0.0

            # ——— Key / Tonalidade ———
            key = None
            scale = None
            key_strength = 0.0
            try:
                key, scale, key_strength = self.key_extractor(audio)
            except Exception:
                key = None
                scale = None
                key_strength = 0.0

            # Listas para agregação de frames
            mfccs, centroids, zcrs = [], [], []
            energies, rms_vals, loud_vals = [], [], []
            rolloffs, flatnesses, fluxes = [], [], []
            contrasts, dissonances = [], []
            chroma_bins = []

            prev_mag = None

            for frame in FrameGenerator(audio,
                                        frameSize=self.frame_size,
                                        hopSize=self.hop_size,
                                        startFromZero=True):
                win = self.windowing(frame)
                mag = self.spectrum(win)

                # ——— Timbre / MFCC ———
                try:
                    _, mfcc_coeffs = self.mfcc(mag)
                    mfccs.append(mfcc_coeffs)
                except Exception:
                    pass

                # ——— Espectrais básicos ———
                try:
                    centroids.append(self.centroid(mag))
                except Exception:
                    pass

                try:
                    zcrs.append(self.zcr(frame))
                except Exception:
                    pass

                # ——— Dinâmica ———
                try:
                    energies.append(self.energy(frame))
                except Exception:
                    pass

                try:
                    rms_vals.append(self.rms(frame))
                except Exception:
                    pass

                try:
                    loud_vals.append(self.loudness(frame))
                except Exception:
                    pass

                # ——— SpectralFlux ———
                if self.flux is not None and prev_mag is not None:
                    try:
                        fluxes.append(self.flux(mag, prev_mag))
                    except Exception:
                        pass
                prev_mag = mag

                # ——— SpectralRolloff & SpectralFlatness ———
                if self.rolloff is not None:
                    try:
                        rolloffs.append(self.rolloff(mag))
                    except Exception:
                        pass

                if self.flatness is not None:
                    try:
                        flatnesses.append(self.flatness(mag))
                    except Exception:
                        pass

                # ——— SpectralContrast & Dissonance ———
                if self.spectral_contrast is not None:
                    try:
                        contrasts.append(self.spectral_contrast(mag))
                    except Exception:
                        pass

                if self.dissonance is not None:
                    try:
                        dissonances.append(self.dissonance(mag))
                    except Exception:
                        pass

                # ——— Chroma ———
                if self.chromagram is not None:
                    try:
                        chroma_bins.append(self.chromagram(mag))
                    except Exception:
                        pass

            # ——— Agregar estatísticas ———

            # Timbre / MFCC
            if mfccs:
                mfcc_array = np.vstack(mfccs)
                mfcc_mean = np.mean(mfcc_array, axis=0).tolist()
                mfcc_std = np.std(mfcc_array, axis=0).tolist()
            else:
                mfcc_mean = []
                mfcc_std = []

            # Espectrais básicos
            centroid_avg = float(np.mean(centroids)) if centroids else 0.0
            zcr_avg = float(np.mean(zcrs)) if zcrs else 0.0

            # Dinâmica
            energy_avg = float(np.mean(energies)) if energies else 0.0
            rms_avg = float(np.mean(rms_vals)) if rms_vals else 0.0
            loudness_avg = float(np.mean(loud_vals)) if loud_vals else 0.0

            # Rolloff / Flatness / Flux
            rolloff_avg = float(np.mean(rolloffs)) if rolloffs else 0.0
            flatness_avg = float(np.mean(flatnesses)) if flatnesses else 0.0
            flux_avg = float(np.mean(fluxes)) if fluxes else 0.0

            # Spectral Contrast / Dissonance
            contrast_mean = (np.mean(np.vstack(contrasts), axis=0).tolist()
                             if contrasts else [])
            dissonance_avg = float(np.mean(dissonances)) if dissonances else 0.0

            # Chroma
            chroma_mean = (np.mean(np.vstack(chroma_bins), axis=0).tolist()
                           if chroma_bins else [])
            chroma_std = (np.std(np.vstack(chroma_bins), axis=0).tolist()
                          if chroma_bins else [])

            # Crest Factor (se existir)
            crest_val = 0.0
            if self.crest is not None:
                try:
                    crest_val = float(self.crest(audio))
                except Exception:
                    crest_val = 0.0

            # ——— Deep Embeddings (VGGish) ———
            vggish_mean = []
            if self.tf_vggish is not None:
                try:
                    audio16k = self.resample16k(audio)
                    vggish_embs = []
                    patch = []
                    wv = self.windowing
                    sp = self.spectrum
                    mbv = self.mel_bands_vgg
                    for frame in FrameGenerator(audio16k,
                                                frameSize=400,
                                                hopSize=160,
                                                startFromZero=True):
                        magvgg = sp(wv(frame))
                        melvgg = mbv(magvgg)
                        patch.append(melvgg)
                        if len(patch) == 64:
                            arr = np.stack(patch, axis=0)           # (64, 96)
                            arr = np.transpose(arr)                 # (96, 64)
                            arr = arr[np.newaxis, ..., np.newaxis]  # (1, 96, 64, 1)
                            emb128 = self.tf_vggish(arr)
                            vggish_embs.append(np.squeeze(emb128))
                            patch = []
                    if vggish_embs:
                        vggish_mean = np.mean(np.vstack(vggish_embs), axis=0).tolist()
                except Exception:
                    vggish_mean = []

            return {
                "bpm": bpm,
                "tempo_confidence": confidence,
                "beats_count": len(beats),
                "onset_rate": onset_rate,
                "harmonic_percussive_ratio": hp_ratio,
                "key": key,
                "scale": scale,
                "key_strength": key_strength,
                "timbral": {
                    "mfcc_mean": mfcc_mean,
                    "mfcc_std": mfcc_std
                },
                "spectral": {
                    "centroid_avg": centroid_avg,
                    "zcr_avg": zcr_avg,
                    "rolloff_avg": rolloff_avg,
                    "flatness_avg": flatness_avg,
                    "flux_avg": flux_avg,
                    "contrast_mean": contrast_mean,
                    "dissonance_avg": dissonance_avg
                },
                "chroma": {
                    "chroma_mean": chroma_mean,
                    "chroma_std": chroma_std
                },
                "dynamics": {
                    "energy_avg": energy_avg,
                    "rms_avg": rms_avg,
                    "loudness_avg": loudness_avg,
                    "crest_factor": crest_val
                },
                "deep_embeds": {
                    "vggish": vggish_mean
                }
            }

        except Exception as e:
            # Em caso de erro, retornar a string de erro e traceback para depuração
            return {
                "error": str(e),
                "trace": traceback.format_exc()
            }
