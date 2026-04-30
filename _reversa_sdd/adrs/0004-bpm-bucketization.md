# ADR 0004: Bucketização de BPM com Targets Fixos

- **Status:** Aceito (Retroativo)
- **Data:** 2025-05-12 (via Commits iniciais de Versão 2)
- **Autor:** DJ

## Contexto
DJs precisam de faixas em velocidades específicas para criar transições perfeitas. Ajustar cada faixa individualmente durante a performance é trabalhoso.

## Decisão
Normalizar todas as faixas para "baldes" (buckets) fixos de 20 BPM, utilizando um offset que favorece velocidades padrão (ex: 120, 140, 160).

## Alternativas Consideradas
- **Preservar BPM Original:** Deixa a cargo do usuário o ajuste de tempo no momento da mixagem.
- **Normalização Linear (ex: Round para o 10 mais próximo):** Criaria muitos baldes pequenos, dificultando a organização.

## Consequências
- **Positivas:** Coleção de música pronta para uso (Plug & Play) para sets de DJ. Organização impecável no sistema de arquivos.
- **Negativas:** Algumas faixas podem sofrer distorção audível se o ajuste de tempo (time-stretch) for muito agressivo (superior a 10-15%).
