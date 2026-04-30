# Domínio e Regras de Negócio — BFX

> Gerado pelo Detective em 2026-04-30
> Nível de Documentação: **Detalhado**

## 📖 Glossário de Domínio

- **Track (Faixa):** A unidade fundamental do sistema. Representa um vídeo musical do YouTube processado.
- **BPM (Beats Per Minute):** Pulsação rítmica da música.
- **Target BPM:** O BPM de destino para o qual a faixa será ajustada via time-stretching.
- **Engagement Rate (Taxa de Engajamento):** Métrica que combina interações (likes/comments) em relação ao volume de visualizações.
- **Scoring (Pontuação):** Algoritmos de ranking para identificar a qualidade e relevância de uma faixa.
- **Sampling (Amostragem):** Geração de um trecho curto (15s) para audição rápida.
- **Bucketization (Agrupamento):** Técnica de agrupar faixas em "baldes" de BPM fixos para facilitar mixagem.

## ⚖️ Regras de Domínio (Business Rules)

### 1. Seleção e Curadoria (The Triple Threat) 🟢 CONFIRMADO
O sistema não baixa todas as faixas de uma playlist. Ele aplica três filtros distintos para maximizar a qualidade:
- **Regra Viral:** Seleciona as faixas com maior volume absoluto de `view_count`.
- **Regra de Engajamento Linear (Alt):** Prioriza faixas com alto volume de comentários por visualização, penalizando fortemente vídeos muito populares (procura por "pérolas escondidas").
- **Regra de Engajamento Logarítmico (Log):** Similar à Alt, mas com penalização suave para vídeos populares (procura por hits de alta qualidade).

### 2. Normalização Temporal 🟢 CONFIRMADO
Para evitar que vídeos antigos dominem o ranking apenas pelo acúmulo histórico de visualizações:
- Todas as métricas (`views`, `likes`, `comments`) são divididas por um fator de peso baseado na idade: `log(age_days + 2)`.

### 3. Estratégia de Snap de BPM 🟢 CONFIRMADO
O sistema impõe uma grade rítmica (grid) para as faixas:
- As faixas são agrupadas em intervalos de 20 BPM.
- O **BPM-alvo** é sempre o início do intervalo somado a um offset fixo (75% do tamanho do intervalo).
- Exemplo: Uma faixa de 118 BPM cai no balde 105-125 e é "travada" em 120 BPM.

### 4. Gestão de Armazenamento (Fail-Fast & Cleanup) 🟢 CONFIRMADO
- Arquivos temporários de formatos conflitantes (`.webm`, `.m4a`) são limpos antes do download.
- O arquivo `.wav` de alta qualidade é **deletado imediatamente** após a conversão para MP3 com time-stretch para preservar espaço em disco.

### 5. Hierarquia de Armazenamento 🟢 CONFIRMADO
- Os arquivos finais são organizados em uma estrutura de diretórios invertida: `music/<BPM_TARGET>/<GENRE>/<SAFE_TITLE>.mp3`.

## 🟡 Inferências e Lacunas

- **Direitos Autorais (Copyright):** O sistema não possui lógica de verificação de licença, assumindo que o uso é para fins de análise ou uso pessoal.
- **Metadata Source:** O YouTube é a única fonte da Verdade (SSOT). Não há integração com APIs como Spotify ou MusicBrainz para enriquecimento de metadados.
- **Concorrência de Download:** A lógica atual sugere um processamento sequencial para evitar bloqueios de IP pelo YouTube.
