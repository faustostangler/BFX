# PlaylistManager

## Visão Geral
Componente responsável pela interface com o YouTube para descoberta de faixas e extração de metadados de engajamento social. Realiza o cálculo de scores que orientam a curadoria.

## Responsabilidades
- Extrair URLs de vídeos de uma playlist do YouTube. 🟢
- Obter metadados detalhados (visualizações, curtidas, comentários, data de publicação). 🟢
- Calcular scores de engajamento (Rate, Alt, Log) com normalização temporal. 🟢
- Sanitizar títulos de vídeos para nomes de arquivos seguros. 🟢

## Interface
- **Entrada:** URL da playlist ou do vídeo.
- **Saída:** Lista de objetos `TrackDTO` preenchidos com metadados e scores.

## Regras de Negócio
- **Normalização por Idade:** Divide as métricas por `log(age_days + 2)` para nivelar vídeos novos e antigos. 🟢
- **Scoring Alt:** `0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * (views / 10M)`. Prioriza nicho. 🟢
- **Scoring Log:** `0.7 * comment_rate + 0.3 * comment_to_like - 1.0 * log(views / 10M)`. Equilíbrio. 🟢
- **Sanitização:** Remove emojis, aspas e caracteres especiais do título. 🟢

## Fluxo Principal
1. Receber URL.
2. Usar `yt-dlp --flat-playlist` para listar URLs.
3. Para cada URL, extrair metadados JSON completos.
4. Calcular dias desde a publicação.
5. Calcular `engagement_rate`, `score_alt` e `score_log`.
6. Retornar lista de `TrackDTO`.

## Fluxos Alternativos
- **Vídeo sem comentários/likes:** Atribui score 0 ou penaliza conforme a fórmula (trata divisão por zero). 🟢
- **URL inválida:** O `yt-dlp` lança erro; o componente deve retornar lista vazia ou erro capturável. 🟢

## Dependências
- `yt-dlp` (CLI tool) — Extração de metadados.
- `math` (Python lib) — Cálculos logarítmicos.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Performance | Uso de `--flat-playlist` para extração inicial rápida. | `playlist.py:50` | 🟢 |
| Precisão | Uso de `math.log1p` para evitar erros com valores zero. | `playlist.py:95` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Extração de Metadados com Sucesso
```gherkin
Dado uma URL de vídeo válida
Quando o PlaylistManager extrai as entradas
Então o objeto TrackDTO deve conter view_count, like_count e comment_count
E o score_alt deve ser calculado conforme a fórmula de penalização linear.
```

### Cenário 2: Normalização de Idade
```gherkin
Dado dois vídeos com o mesmo engajamento absoluto
Quando um é de hoje e o outro de 1 ano atrás
Então o vídeo de hoje deve ter um score final maior.
```

## Cenários de Borda
1. **Vídeo com estatísticas desativadas:** O YouTube não retorna `like_count` ou `comment_count`. O sistema deve assumir 0 e não quebrar. 🔴
2. **Vídeo "Unlisted" ou Privado:** O extrator deve identificar a falha de acesso e pular o item. 🟢

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Extração de URLs | Must | Base para todo o pipeline. |
| Cálculo de Scores | Must | Essencial para a curadoria automatizada. |
| Sanitização de Títulos | Should | Evita erros de I/O mas não afeta a lógica musical. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/playlist.py` | `PlaylistManager` | 🟢 |
| `beatforge/playlist.py` | `compute_engagement_scores` | 🟢 |
