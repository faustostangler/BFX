# Dependências do Projeto — BFX

> Gerado pelo Scout em 2026-04-30

## 📦 Dependências Críticas

| Pacote | Versão | Função |
| :--- | :--- | :--- |
| `python` | `3.12` | Runtime principal |
| `librosa` | `0.11.0` | Processamento e análise de áudio (BPM, Onsets) |
| `tensorflow` | `2.19.0` | Infraestrutura para modelos de ML |
| `keras` | `3.10.0` | Interface para modelos neurais |
| `pandas` | `2.2.3` | Manipulação de metadados e CSVs |
| `numpy` | `1.26.4` | Computação numérica |
| `yt-dlp` | `2025.4.30` | Download de áudio e extração de metadados do YouTube |
| `soundfile` | `0.13.1` | Leitura e escrita de arquivos WAV |
| `ffmpeg` | `(system)` | Processamento de áudio (conversão, sampling) |
| `rich` | `14.0.0` | Interface de linha de comando (CLI) |

## 🛠️ Gerenciamento e Infra

- **Gerenciador de Pacotes:** `uv` (identificado via Dockerfile e Makefile)
- **Containerização:** Docker (com volumes para música e dados)
- **Compilação de Bytecode:** Habilitada via `UV_COMPILE_BYTECODE` no Dockerfile.
