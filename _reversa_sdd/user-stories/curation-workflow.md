# User Story: Fluxo de Curadoria Social

> Gerado pelo Writer em 2026-04-30

## 📝 Descrição
Como um **DJ / Curador Musical**, eu quero que o sistema analise automaticamente playlists do YouTube e selecione as faixas com maior potencial de engajamento e qualidade rítmica, para que eu possa focar apenas nas músicas que realmente importam para o meu set.

## 🎭 Personas
- **DJ Pedro:** Especialista em música eletrônica que busca "hidden gems" (pérolas escondidas) com alto engajamento em canais de nicho.
- **Curadora Ana:** Gerente de rádio que precisa dos hits mais populares (virais) para a programação mainstream.

## 🗺️ Fluxo do Usuário
1. O usuário edita o arquivo `playlist.txt` adicionando links de playlists ou vídeos individuais.
2. O usuário executa o comando principal do sistema.
3. O sistema extrai metadados de **todas** as faixas da playlist (sem baixar o áudio ainda).
4. O sistema aplica os algoritmos de scoring (Alt, Log, Viral).
5. O sistema apresenta um relatório ou prossegue automaticamente com o download apenas das Top-N faixas de cada categoria.

## ✅ Critérios de Aceitação

### Cenário 1: Descoberta de Hits de Nicho (Estratégia ALT)
- **Dado** uma playlist com 100 vídeos.
- **Quando** o sistema aplica o `Engagement Score Alt`.
- **Então** ele deve priorizar vídeos com alta razão de Comentários/Views, mesmo que tenham poucas views absolutas.
- **E** ele deve penalizar vídeos virais massivos com baixo engajamento relativo.

### Cenário 2: Normalização por Recência
- **Dado** dois vídeos com o mesmo número de interações.
- **Quando** um vídeo foi lançado ontem e o outro há 5 anos.
- **Então** o vídeo de ontem deve aparecer no topo do ranking devido ao peso de idade (`age_weight`).

### Cenário 3: Evitar Duplicidade de Trabalho
- **Dado** que 10 vídeos da playlist já foram analisados em execuções anteriores.
- **Quando** o processo de curadoria inicia.
- **Então** o sistema deve ignorar esses vídeos na fase de extração pesada e focar apenas nas novas URLs.

## 🔴 Cenários de Borda
- **Playlist Privada:** O sistema deve informar que não tem acesso à playlist e encerrar o fluxo daquela URL graciosamente.
- **Vídeo com Comentários Desativados:** O sistema deve tratar o campo `comment_count` como 0 e ainda assim calcular o score baseado em `likes`.
