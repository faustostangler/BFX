# Máquina de Estados: Ciclo de Vida da Faixa — BFX

> Gerado pelo Detective em 2026-04-30

A entidade **Track** (Faixa) atravessa múltiplos estados desde a descoberta em uma playlist até a geração da amostra final. Embora não haja um campo de status explícito no banco, o estado é inferido pela presença de dados em colunas específicas.

## 🔄 Fluxo de Processamento

```mermaid
state_machine
    [*] --> Discovered: URL identificada na playlist
    Discovered --> Metadata_Extracted: yt-dlp extrai views/likes/tags
    Metadata_Extracted --> Selected: Passa nos filtros de Scoring (Viral/Alt/Log)
    Selected --> Downloaded: WAV salvo em disco
    Downloaded --> Features_Extracted: Essentia processa DSP + VGGish
    Features_Extracted --> Analyzed: BPM detectado e Target definido
    Analyzed --> Converted: MP3 com time-stretch gerado
    Converted --> Sampled: Preview de 15s criado
    Sampled --> [*]: Fluxo completo
    
    Selected --> Failed: Erro de rede ou indisponibilidade
    Analyzed --> Failed: Erro no FFmpeg ou Essentia
```

## 📋 Estados e Gatilhos

| Estado | Evidência (Banco de Dados) | Gatilho |
| :--- | :--- | :--- |
| **Discovered** | Registro com `url` | `PlaylistManager.fetch_entries` |
| **Metadata_Extracted** | `view_count`, `engagement_rate` preenchidos | `PlaylistManager.fetch_entries` (Full extract) |
| **Selected** | Track persistida no banco final | `BeatForgeRunner.run` (Filtro de Curação) |
| **Downloaded** | `wav_path` preenchido | `Downloader.download_to_wav` |
| **Features_Extracted** | `bpm_essentia`, `key`, `dynamics` preenchidos | `EssentiaFeatureExtractor.extract_all` |
| **Analyzed** | `bpm_librosa`, `target_bpm` preenchidos | `BPMAnalyzer.extract` e `choose_target` |
| **Converted** | `mp3_path` preenchido | `Converter.convert` |
| **Sampled** | Arquivo `*_sample.mp3` existe em disco | `Sampler.create_sample` |

## 🔴 Lacunas Identificadas
- O sistema não possui um mecanismo de **Retry** automático para o estado `Failed`.
- Não há marcação de **"Processed"** atômica; o sistema assume que se os BPMs estão lá, a faixa está pronta.
