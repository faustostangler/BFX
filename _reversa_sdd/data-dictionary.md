# Dicionário de Dados — BFX

> Gerado pelo Archaeologist em 2026-04-30
> Fonte: `beatforge/persistence.py` e `beatforge/track.py`

## 📊 Entidade Principal: `track_info`

Esta tabela armazena o estado completo de cada faixa processada, desde metadados de rede até features acústicas profundas.

### 1. Metadados e Identificação
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `url` | TEXT | **Chave Primária**. URL única do vídeo no YouTube. |
| `title` | TEXT | Título original extraído. |
| `artist` | TEXT | Artista/Canal extraído. |
| `album` | TEXT | Álbum (se disponível). |
| `genre` | TEXT | Gênero musical definido no processamento. |
| `safe_title` | TEXT | Título sanitizado para uso em nomes de arquivos. |

### 2. Métricas de Engajamento
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `view_count` | INTEGER | Contagem de visualizações (normalizada por idade). |
| `like_count` | INTEGER | Contagem de curtidas (normalizada por idade). |
| `comment_count` | INTEGER | Contagem de comentários (normalizada por idade). |
| `engagement_rate` | REAL | Taxa de engajamento baseada em soma ponderada. |
| `engagement_score_alt` | REAL | Score com penalização linear de popularidade. |
| `engagement_score_log` | REAL | Score com penalização logarítmica de popularidade. |
| `age_weight` | REAL | Fator aplicado para normalização temporal. |

### 3. Caminhos e Processamento
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `wav_path` | TEXT | Caminho do arquivo WAV temporário. |
| `mp3_path` | TEXT | Caminho final do arquivo MP3 (na pasta de target_bpm). |
| `target_bpm` | INTEGER | BPM objetivo após conversão (bucket). |

### 4. Análise Rítmica e Tonal
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `bpm_librosa` | REAL | BPM detectado pela engine Librosa. |
| `bpm_essentia` | REAL | BPM detectado pela engine Essentia. |
| `tempo_confidence` | REAL | Nível de confiança na detecção do tempo (0-1). |
| `beats_count` | INTEGER | Número total de batidas detectadas. |
| `onset_rate` | REAL | Frequência de inícios de notas por segundo. |
| `key` | INTEGER | Nota fundamental (Índice Essentia). |
| `scale` | INTEGER | Escala (0=major, 1=minor). |
| `key_strength` | REAL | Confiança na detecção da tonalidade. |

### 5. Features Acústicas (DSP)
| Campo | Tipo | Descrição |
| :--- | :--- | :--- |
| `timbral_mfcc_mean` | TEXT (JSON) | Média dos 13 coeficientes MFCC. |
| `spectral_centroid_avg` | REAL | Centro de massa do espectro (brilho). |
| `spectral_rolloff_avg` | REAL | Frequência abaixo da qual 85% da energia reside. |
| `dynamics_loudness_avg` | REAL | Volume percebido (LUFS). |
| `harmonic_percussive_ratio`| REAL | Relação entre energia harmônica e percussiva. |
| `deep_embeds_vggish` | TEXT (JSON) | Vetor de 128 dimensões do modelo VGGish. |

---

## 📂 Estrutura de Arquivos (DTOs)

### `TrackDTO` (Python Class)
- Mapeia 1:1 com a tabela `track_info`.
- Implementada via `dataclasses` (inferido) ou `class` simples em `beatforge/track.py`.
