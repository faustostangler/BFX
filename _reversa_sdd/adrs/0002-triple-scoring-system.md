# ADR 0002: Sistema de Scoring Triplo (Alt/Log/Viral)

- **Status:** Aceito (Retroativo)
- **Data:** 2025-05-14 (via Commits `760ebd8` a `459444e`)
- **Autor:** DJ

## Contexto
O YouTube possui muitos vídeos com milhões de visualizações que não possuem qualidade musical ou relevância artística (ex: memes, clickbaits). Basear-se apenas no `view_count` resulta em playlists de baixa qualidade.

## Decisão
Implementar três métricas de seleção simultâneas para garantir diversidade e qualidade:
1. **Viral:** Popularidade bruta.
2. **Alt:** Engajamento intenso (comentários/likes) penalizando visualizações (encontra tendências de nicho).
3. **Log:** Equilíbrio entre popularidade e engajamento.

## Alternativas Consideradas
- **Single Metric (Likes/Views):** Frequentemente enviesada por vídeos muito antigos.
- **Manual Curation:** Inviável para processar centenas de playlists e milhares de faixas.

## Consequências
- **Positivas:** Descoberta de faixas de alta qualidade que ainda não são hits globais. Redução de ruído (vídeos virais sem engajamento real).
- **Negativas:** Maior complexidade computacional e necessidade de extrair metadados completos de cada vídeo antes de decidir pelo download.
