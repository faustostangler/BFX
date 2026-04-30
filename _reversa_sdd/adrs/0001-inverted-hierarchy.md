# ADR 0001: Hierarquia de Pastas Invertida (BPM/Gênero)

- **Status:** Aceito (Retroativo)
- **Data:** 2026-04-22 (via Commit `b2454ac`)
- **Autor:** DJ

## Contexto
Originalmente, o sistema armazenava arquivos de áudio em pastas baseadas no gênero ou na playlist de origem. No entanto, para fins de mixagem e uso por DJs, a característica rítmica (BPM) é o critério de busca primário.

## Decisão
Inverter a hierarquia de armazenamento para priorizar o BPM-alvo. A nova estrutura é:
`music/<BPM_TARGET>/<GENRE>/<FILE>.mp3`

## Alternativas Consideradas
- **Hierarquia por Gênero:** Dificulta a localização de faixas compatíveis rítmicos durante uma sessão ao vivo.
- **Flat Folder com Prefixos:** Resultaria em milhares de arquivos em uma única pasta, degradando a performance do sistema de arquivos e a navegabilidade.

## Consequências
- **Positivas:** Facilidade extrema para encontrar faixas que "batem" no mesmo tempo. Organização automática por "baldes" de velocidade.
- **Negativas:** Requer movimentação de arquivos se o BPM de uma faixa for re-analisado ou se o algoritmo de bucketização mudar.
