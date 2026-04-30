# Orchestrator (BeatForgeRunner)

## Visão Geral
O orquestrador central do sistema. É responsável por coordenar todo o pipeline de processamento de áudio, desde a leitura da lista de URLs até a conversão final e limpeza de arquivos.

## Responsabilidades
- Ler e validar arquivos de entrada de playlists (`playlist.txt`). 🟢
- Coordenar a curadoria de faixas usando múltiplas estratégias de scoring. 🟢
- Gerenciar o ciclo de vida de processamento de cada faixa (download -> análise -> conversão). 🟢
- Realizar a limpeza de arquivos temporários e logs de progresso. 🟢

## Interface
- **Entrada:** Caminho para arquivo de texto com URLs do YouTube e nomes de pastas.
- **Saída:** Biblioteca de áudio organizada em disco e banco de dados SQLite atualizado.
- **Configuração:** Injeção de dependências (Downloader, Analyzer, etc.) via construtor.

## Regras de Negócio
- Somente processa URLs que ainda não possuem análise de BPM no banco de dados. 🟢
- Aplica três estratégias de seleção: `Top Alt`, `Top Log` e `Top Viral`. 🟢
- Organiza a saída em pastas baseadas no `target_bpm` e `genre`. 🟢
- Se houver erro em uma faixa, registra o erro e continua para a próxima (não interrompe o processo). 🟢

## Fluxo Principal
1. Carregar playlists do arquivo de entrada.
2. Extrair metadados e calcular scores para todas as novas URLs.
3. Selecionar as melhores faixas baseadas nos limites configurados.
4. Para cada faixa selecionada:
    a. Baixar áudio como WAV.
    b. Extrair BPM e características acústicas.
    c. Calcular BPM alvo (bucket).
    d. Converter para MP3 com time-stretch.
    e. Gerar amostra de 15s.
    f. Deletar WAV original.
5. Salvar estado final no banco de dados.

## Fluxos Alternativos
- **Arquivo de entrada vazio:** O sistema encerra graciosamente informando "No tracks to process". 🟢
- **Playlist com erro de rede:** O componente captura `Exception`, loga o traceback e pula para a próxima entrada. 🟢

## Dependências
- `PlaylistManager` — Extração e scoring de metadados.
- `Downloader` — Aquisição de áudio bruto.
- `BPMAnalyzer` — Detecção de tempo.
- `Converter` — Ajuste rítmico e compressão.
- `Sampler` — Criação de previews.
- `Persistence` — Persistência de estado.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Performance | Timeouts de 5 min para download e 2 min para análise de áudio. | [Validação Humana] | 🟢 |
| Segurança | Sanitização de títulos para nomes de arquivos seguros. | `main.py:100` (`make_safe_title`) | 🟢 |
| Disponibilidade | Auto-recovery do banco de dados em caso de corrupção. | [Validação Humana] | 🟢 |

## Critérios de Aceitação

### Cenário 1: Happy Path de Processamento Completo
```gherkin
Dado um arquivo "playlist.txt" com 1 URL válida de 120 BPM
Quando o BeatForgeRunner é executado
Então o arquivo "music/120/Genre/Title.mp3" deve ser criado
E o arquivo "Title_sample.mp3" deve estar presente
E o arquivo WAV temporário deve ser removido.
```

### Cenário 2: Faixa Já Processada
```gherkin
Dado que uma URL já existe no banco de dados com BPM extraído
Quando o BeatForgeRunner processa a playlist
Então o sistema deve pular o download e análise desta URL.
```

### Cenário 3: Erro no Download (Cenário de Borda)
```gherkin
Dado uma URL do YouTube protegida ou inexistente
Quando o Downloader falha em baixar o áudio
Então o orquestrador deve capturar a exceção
E não deve criar registro de áudio no banco
E deve prosseguir para a próxima URL da lista.
```

## Cenários de Borda
1. **URL de Live Stream:** O `yt-dlp` pode falhar ou gerar arquivo infinito; o sistema deve tratar o timeout do subprocesso (atualmente lacuna 🔴).
2. **Playlist Gigante (>1000 itens):** O cálculo de scores em memória pode degradar a performance; o sistema não possui paginação de análise inicial 🔴.

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Orquestração de Fluxo | Must | Sem isso o sistema não executa o pipeline. |
| Curadoria de Faixas (Scoring) | Must | Diferencial do sistema para qualidade da biblioteca. |
| Limpeza de WAVs | Should | Importante para economia de disco, mas não impede o funcionamento core. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `main.py` | `BeatForgeRunner` | 🟢 |
| `main.py` | `main` (CLI Entry point) | 🟢 |
