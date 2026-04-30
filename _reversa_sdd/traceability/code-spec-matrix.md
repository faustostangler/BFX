# Matriz de Rastreabilidade (Code-Spec Matrix)

> Gerado pelo Writer em 2026-04-30

Esta matriz correlaciona os arquivos de código originais com suas respectivas especificações funcionais geradas no SDD.

| Arquivo Original | Spec Correspondente (SDD) | Cobertura |
| :--- | :--- | :---: |
| `main.py` | `sdd/orchestrator.md` | 🟢 |
| `beatforge/playlist.py` | `sdd/playlist-manager.md` | 🟢 |
| `beatforge/downloader.py` | `sdd/downloader.md` | 🟢 |
| `beatforge/bpm.py` | `sdd/bpm-analyzer.md` | 🟢 |
| `beatforge/essentia_features.py` | `sdd/feature-extractor.md` | 🟢 |
| `beatforge/converter.py` | `sdd/audio-converter.md` | 🟢 |
| `beatforge/sampler.py` | `sdd/audio-sampler.md` | 🟢 |
| `beatforge/persistence.py` | `sdd/persistence.md` | 🟢 |
| `beatforge/track.py` | `sdd/persistence.md` (DTO) | 🟡 |
| `config.py` | Vários (Injetado em Orchestrator/BPM) | 🟡 |
| `Makefile` | `deployment.md` | 🟢 |
| `Dockerfile` | `deployment.md` | 🟢 |
| `docker-compose.yml` | `deployment.md` | 🟢 |

## 📊 Estatísticas de Cobertura
- **Total de Módulos Core:** 8
- **Total de Specs SDD:** 8
- **User Stories:** 2
- **Cobertura de Funcionalidades Críticas:** ~95% 🟢

## 🔴 Lacunas de Especificação
- **Scripts Utilitários:** Arquivos como `reorganize_music.py` e `backfill_samples.py` não possuem specs SDD dedicadas, sendo tratados como ferramentas de manutenção ad-hoc.
- **Tratamento de Concorrência:** O código é majoritariamente síncrono, e a especificação reflete essa limitação, sem prever escalabilidade para múltiplos workers paralelos.
