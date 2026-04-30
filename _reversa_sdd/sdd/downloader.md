# Downloader

## Visão Geral
Componente de infraestrutura que gerencia a aquisição física do áudio do YouTube e sua extração para o formato WAV de alta fidelidade (PCM).

## Responsabilidades
- Realizar o download do fluxo de áudio do YouTube usando `yt-dlp`. 🟢
- Converter o fluxo para WAV (16-bit, Mono ou Stereo conforme config). 🟢
- Garantir que arquivos conflitantes de tentativas anteriores sejam removidos. 🟢
- Implementar polling de espera para garantir que o arquivo foi escrito em disco antes de liberar o processo. 🟢

## Interface
- **Entrada:** `url` do vídeo e `safe_title` (para nome de arquivo).
- **Saída:** Caminho absoluto para o arquivo `.wav` gerado.

## Regras de Negócio
- **Pre-cleanup:** Antes de iniciar o download, o componente busca e deleta arquivos com o mesmo nome e extensões `.webm`, `.m4a`, `.mp3`, `.mp4` e `.wav`. 🟢
- **Extração de Áudio:** Força o `yt-dlp` a extrair apenas o áudio (`--extract-audio`) e converter para wav (`--audio-format wav`). 🟢
- **Sincronia de Escrita:** Implementa `_wait_for_file` que checa a existência do arquivo a cada 1s por até 30s para evitar Race Conditions. 🟢

## Fluxo Principal
1. Receber URL e título.
2. Executar `_cleanup_conflicts`.
3. Montar comando `yt-dlp` com parâmetros de extração e output template.
4. Executar subprocesso.
5. Chamar `_wait_for_file`.
6. Retornar caminho do arquivo se sucesso, ou lançar `TimeoutError`.

## Fluxos Alternativos
- **Vídeo indisponível (Copyright/Private):** O subprocesso retorna código de erro; o componente captura e propaga a exceção. 🟢
- **Timeout de download:** Se o arquivo não aparecer após 30s de polling, o sistema desiste da faixa. 🟢

## Dependências
- `yt-dlp` (CLI) — Motor de download.
- `ffmpeg` (CLI) — Motor de conversão interna usado pelo yt-dlp.
- `subprocess` (Python lib) — Execução de comandos externos.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Performance | Timeout de 5 minutos (300s) para o processo de download. | [Validação Humana] | 🟢 |
| Confiabilidade | Polling de 30s para garantir persistência em disco (Wait for File). | `downloader.py:92` | 🟢 |
| Limpeza | Deleção preventiva de arquivos residuais. | `downloader.py:79` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Download e Conversão com Sucesso
```gherkin
Dado uma URL válida e um diretório de saída
Quando o download_to_wav é invocado
Então o yt-dlp deve ser executado
E um arquivo .wav válido deve estar presente no diretório ao final.
```

### Cenário 2: Tratamento de Conflitos
```gherkin
Dado que existe um arquivo "musica.mp3" residual no diretório
Quando o downloader inicia o processamento de "musica"
Então o arquivo "musica.mp3" deve ser deletado antes do novo download começar.
```

## Cenários de Borda
1. **Espaço em disco insuficiente:** O download falhará no meio do processo. O sistema deve capturar o erro do subprocesso. 🟡
2. **Conexão instável:** O `yt-dlp` possui retentativas internas, mas o componente BFX pode sofrer timeout se o processo total exceder o limite esperado. 🟡

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Extração de Áudio (WAV) | Must | Sem o arquivo bruto, não há análise de BPM nem conversão final. |
| Polling de Arquivo | Should | Evita erros de "arquivo não encontrado" em sistemas de arquivos lentos. |
| Pre-cleanup | Should | Evita colisão de nomes e falha de escrita. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/downloader.py` | `Downloader` | 🟢 |
| `beatforge/downloader.py` | `_wait_for_file` | 🟢 |
