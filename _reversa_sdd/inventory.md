# Inventário do Projeto — BFX

> Gerado pelo Scout em 2026-04-30

## 📂 Estrutura de Pastas (Módulos Principais)

- `beatforge/` — **Core Domain**. Contém a lógica de download, análise de áudio, processamento de BPM e persistência.
- `scripts/` — **Utilities**. Scripts de manutenção e tarefas em lote (ex: backfill de samples).
- `tests/` — **Testing**. Estrutura para testes unitários e de integração (atual: vazio/cache).
- `music/`, `Music 120/`, `Music 160/`, `music_old/` — **Assets**. Repositórios de áudio processados e originais.

## 🛠️ Tecnologias e Frameworks

- **Linguagem Principal:** Python 3.12 (14 arquivos .py)
- **Análise de Áudio:** librosa, Essentia (inferido via entry points e deps)
- **Machine Learning:** TensorFlow, Keras (para extração de features complexas)
- **Manipulação de Dados:** Pandas, NumPy
- **Download:** yt-dlp (YouTube downloader)
- **Persistência:** SQLite (playlist.db)
- **Infraestrutura:** Docker (slim image), uv (package manager)

## 🚀 Pontos de Entrada (Entry Points)

- `main.py` — Orquestrador principal do pipeline.
- `Makefile` — Comandos de automação (up, build, shell, local-run).
- `Dockerfile` — Definição da imagem de execução.
- `docker-compose.yml` — Orquestração de containers e volumes.

## 💾 Banco de Dados

- `playlist.db` — Banco SQLite centralizado.
- `track_info.csv` — Backup/Exportação de metadados.

## 🧪 Testes

- **Framework:** Pytest (identificado em requirements e cache).
- **Contagem:** 0 arquivos encontrados (cache indica existência prévia de `test_sampler.py`).
- **Status:** Sem cobertura ativa detectada no momento.
