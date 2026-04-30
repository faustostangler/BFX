# Arquitetura do Sistema — BFX (BeatForge)

> Gerado pelo Architect em 2026-04-30
> Nível de Documentação: **Detalhado**

## 🎯 Objetivo e Contexto
O BFX é um sistema de engenharia de áudio e curadoria musical projetado para automatizar a criação de bibliotecas rítmicas para DJs. Ele resolve o problema da aquisição manual de faixas, detecção de BPM e ajuste de tempo (time-stretching) para baldes de velocidade padronizados.

## 🏗️ Estrutura de Containers
O sistema opera em uma arquitetura de **Modular Monolith** containerizado:
- **CLI/Orchestrator:** Ponto de entrada que gerencia o estado e o fluxo entre playlists.
- **Audio Engine:** Camada DSP (Essentia/Librosa/FFmpeg) para análise e transformação.
- **Persistence Layer:** SQLite para armazenamento de metadados e features.

## 🔗 Integrações
- **YouTube (yt-dlp):** Extração de áudio e metadados de engajamento social.
- **FFmpeg:** Motor de processamento de sinal (conversão, time-stretch, sampling).
- **Essentia/TensorFlow:** Motor de análise acústica profunda e geração de embeddings musicais.

## 📊 Modelo de Dados
O modelo de dados é centrado na entidade `Track`, que consolida metadados de rede, análise rítmica e características acústicas. Embora armazenado em uma tabela única por simplicidade, logicamente divide-se em:
1. **Identidade** (URL, Title, Artist)
2. **Engajamento** (Scores Alt/Log/Viral)
3. **Análise** (BPM, Key, Features)
4. **Assets** (Paths MP3/Sample)

## 🚀 Estratégia de Deployment
Deployment via Docker Compose com volumes persistentes para garantir que a biblioteca musical e o banco de metadados sobrevivam a reinicializações dos containers.

---

Para detalhes técnicos específicos, consulte:
- [C4 Contexto](c4-context.md)
- [C4 Containers](c4-containers.md)
- [C4 Componentes](c4-components.md)
- [ERD Completo](erd-complete.md)
- [Deployment](deployment.md)
- [Matriz de Impacto](traceability/spec-impact-matrix.md)
