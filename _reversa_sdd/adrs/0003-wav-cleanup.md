# ADR 0003: Limpeza de Arquivos WAV Pós-Conversão

- **Status:** Aceito (Retroativo)
- **Data:** 2025-07-27 (via Commit `6c0f552`)
- **Autor:** DJ

## Contexto
Arquivos WAV são descompactados e ocupam cerca de 10x mais espaço que um MP3 de alta qualidade. Com milhares de faixas, o custo de armazenamento torna-se proibitivo.

## Decisão
Deletar o arquivo `.wav` imediatamente após a conclusão bem-sucedida da conversão para MP3 (incluindo o processamento de time-stretch).

## Alternativas Consideradas
- **Manter WAVs em Cold Storage:** Requereria infraestrutura de nuvem adicional ou discos rígidos externos massivos.
- **Download direto para MP3:** O `yt-dlp` permite isso, mas a análise de BPM e a extração de features via Essentia são muito mais precisas e rápidas quando operam sobre arquivos WAV (PCM).

## Consequências
- **Positivas:** Redução drástica (90%) no consumo de disco por faixa processada.
- **Negativas:** Se uma re-conversão for necessária (ex: mudar o target BPM), o arquivo deve ser baixado novamente do YouTube.
