# Audio Sampler

## Visão Geral
Componente responsável por gerar trechos curtos de áudio (previews) a partir das faixas processadas, facilitando a curadoria rápida pelo usuário final.

## Responsabilidades
- Extrair um segmento de tempo fixo de um arquivo MP3. 🟢
- Realizar a extração sem re-codificação pesada para economizar recursos. 🟢
- Organizar as amostras junto aos arquivos originais ou em pasta dedicada. 🟢

## Interface
- **Entrada:** Caminho do arquivo MP3 original e parâmetros de tempo (início, duração).
- **Saída:** Arquivo MP3 de amostra (`*_sample.mp3`).

## Regras de Negócio
- **Janela Padrão:** Extrai 15 segundos de áudio. 🟢
- **Ponto de Início:** Inicia a extração a partir do segundo 30 (offset fixo para pular introduções e chegar ao "refrão" ou corpo da música). 🟢
- **Formato de Saída:** Preserva o formato MP3 original. 🟢

## Fluxo Principal
1. Receber caminho do MP3 processado.
2. Definir o ponto de corte (`-ss 30`).
3. Definir a duração (`-t 15`).
4. Executar comando FFmpeg para copiar o stream de áudio e salvar no novo arquivo.
5. Validar a criação do arquivo.

## Fluxos Alternativos
- **Faixa com menos de 45s de duração:** O FFmpeg extrairá até o fim da faixa; o componente deve tratar para que o comando não falhe se o tempo final for menor que 15s. 🟡
- **Arquivo original corrompido:** O sampler deve reportar o erro e não criar o arquivo de saída. 🟢

## Dependências
- `ffmpeg` (CLI) — Manipulação de frames de áudio.
- `subprocess` (Python lib) — Execução de comandos.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Eficiência | Uso de `-acodec copy` (quando possível) para corte instantâneo. | `sampler.py:25` | 🟡 |

## Critérios de Aceitação

### Cenário 1: Geração de Amostra com Sucesso
```gherkin
Dado um arquivo "musica.mp3" de 3 minutos
Quando o Sampler é executado
Então um arquivo "musica_sample.mp3" deve ser criado
E o arquivo deve ter exatamente 15 segundos
E o áudio deve começar no ponto correspondente ao segundo 30 do original.
```

## Cenários de Borda
1. **Ponto de Início maior que a duração:** Se a música tiver 20s e o sampler tentar começar no 30s, o arquivo gerado será vazio ou falhará. O sistema não valida duração antes de cortar 🔴.

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Extração de Segmento | Should | Funcionalidade de conveniência para audição rápida. |
| Preservação de Bitrate | Could | Ideal para manter a qualidade da amostra igual à original. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/sampler.py` | `Sampler` | 🟢 |
| `beatforge/sampler.py` | `create_sample` | 🟢 |
