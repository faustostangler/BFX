# Análise Técnica de Código — BFX

> Gerado pelo Archaeologist em 2026-04-30
> Nível de Documentação: **Detalhado**

## 🏗️ Visão Geral da Arquitetura (Tactical DDD)

O projeto segue uma estrutura modular onde cada componente em `beatforge/` atua como um serviço especializado, coordenado pelo `BeatForgeRunner` em `main.py`.

### Módulos Analisados

1.  **`beatforge/downloader`** 🟢 CONFIRMADO
    - **Responsabilidade:** Interface com `yt-dlp` e FFmpeg para aquisição de áudio.
    - **Lógica Crítica:** Gestão de conflitos de extensão e polling de disponibilidade de arquivo.
2.  **`beatforge/bpm`** 🟢 CONFIRMADO
    - **Responsabilidade:** Extração de tempo rítmico e bucketização em targets.
    - **Algoritmo:** Dual-engine (Essentia + fallback Librosa) com normalização de oitavas (metade/dobro).
3.  **`beatforge/sampler`** 🟢 CONFIRMADO
    - **Responsabilidade:** Geração de previews de 15 segundos.
    - **Tecnologia:** FFmpeg via subprocess.
4.  **`beatforge/playlist`** 🟢 CONFIRMADO
    - **Responsabilidade:** Extração de metadados e cálculo de engajamento.
    - **Algoritmo:** Scoring de engajamento triplo (Rate, Alt, Log) com compensação de idade do vídeo.
5.  **`beatforge/converter`** 🟢 CONFIRMADO
    - **Responsabilidade:** Time-stretching de áudio para atingir o BPM target.
    - **Algoritmo:** Filtro `atempo` do FFmpeg com fator calculado dinamicamente.
6.  **`beatforge/persistence`** 🟢 CONFIRMADO
    - **Responsabilidade:** Camada de dados SQLite.
    - **Padrão:** Repository simplificado com serialização JSON para campos complexos.
7.  **`beatforge/essentia_features`** 🟢 CONFIRMADO
    - **Responsabilidade:** Extração massiva de características acústicas (DSP + Deep Learning).
    - **Complexidade:** Alta. Gestão de imports dinâmicos e processamento por frames com agregação estatística.

## 🧠 Algoritmos e Lógica de Negócio

### 1. Cálculo de Engajamento (Scoring)
Localizado em `beatforge/playlist.py`, o sistema utiliza uma fórmula que penaliza vídeos "virais" de massa para encontrar "pérolas" com alto engajamento relativo:
- **Engagement Rate:** $(Likes + Comments) / Views \times 10^5$
- **Log Score:** $0.7 \times CommentRate + 0.3 \times CommentToLike - 1.0 \times \log(Views)$
- **Age Weight:** Todos os números são divididos por $\log(age\_days + 2)$ para não prejudicar vídeos novos.

### 2. Normalização e Bucketização de BPM
Localizado em `beatforge/bpm.py`:
- **Normalização:** Se o BPM detectado for $< 45$, multiplica por 2. Se $> 210$, divide por 2.
- **Bucketização:** O target é definido como o início da faixa de 20 BPM + um offset de 15 BPM (75% da faixa). Ex: Faixa 105-125 -> Target 120.

### 3. Extração de Features (DSP Pipeline)
Localizado em `beatforge/essentia_features.py`:
- **Pipeline:** MonoLoader -> FrameGenerator (1024/512) -> Windowing (Hann) -> Spectrum.
- **Deep Embeddings:** Implementa o patch-processing para VGGish (96 bandas mel, patches de 64 frames) para gerar vetores de 128 dimensões.

## ⚠️ Lacunas e Riscos Detectados

- 🔴 **Tratamento de Limites de Tempo (Time-stretch):** O filtro `atempo` do FFmpeg só suporta de 0.5 a 2.0. Ratios fora disso falharão ou produzirão áudio distorcido sem aviso explícito no código atual.
- 🔴 **Concorrência:** O código é inteiramente síncrono. O download e processamento de grandes playlists podem demorar horas sem paralelismo.
- 🟡 **Persistência de Embeddings:** Embeddings VGGish são salvos como strings JSON no SQLite, o que dificulta buscas vetoriais eficientes sem uma extensão como `sqlite-vss`.
