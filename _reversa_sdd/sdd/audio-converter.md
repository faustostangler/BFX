# Audio Converter

## Visão Geral
Componente responsável pela transformação final do áudio, aplicando ajustes de tempo (time-stretching) e normalização para gerar o arquivo MP3 final.

## Responsabilidades
- Converter arquivos WAV para MP3 de alta qualidade (320kbps ou variável conforme config). 🟢
- Aplicar o filtro `atempo` do FFmpeg para ajustar a velocidade do áudio sem alterar o pitch (tom). 🟢
- Garantir que o áudio final tenha o BPM-alvo (Target BPM) definido pelo sistema. 🟢

## Interface
- **Entrada:** Caminho do arquivo WAV, BPM original e Target BPM.
- **Saída:** Caminho do arquivo MP3 gerado na hierarquia de pastas correta.

## Regras de Negócio
- **Calculo de Stretch:** `ratio = target_bpm / original_bpm`. 🟢
- **Time-Stretching:** Usa o filtro `atempo` do FFmpeg. Para ratios fora de 0.5-2.0, aplica múltiplos filtros em cascata (ex: para 4.0x use `atempo=2.0,atempo=2.0`). 🟢
- **Qualidade de Saída:** Codifica em MP3 usando o codec `libmp3lame` com bitrate de 320k. 🟢
- **Target Folder:** Salva o arquivo em `music/<target_bpm>/<genre>/<safe_title>.mp3`. 🟢

## Fluxo Principal
1. Receber WAV e dados rítmicos.
2. Calcular o ratio de velocidade necessário.
3. Criar a estrutura de diretórios de destino se não existir.
4. Montar o comando FFmpeg com a string de filtros `atempo`.
5. Executar subprocesso.
6. Validar se o MP3 foi criado com sucesso.

## Fluxos Alternativos
- **BPM Original == Target BPM:** O sistema pula a etapa de stretch e apenas realiza a conversão para MP3 (ratio 1.0). 🟢
- **Erro no FFmpeg:** Se o subprocesso falhar, o componente captura a saída de erro (stderr) e propaga a exceção. 🟢

## Dependências
- `ffmpeg` (CLI) — Motor de conversão e processamento.
- `subprocess` (Python lib) — Execução de comandos.
- `os` / `pathlib` — Gestão de diretórios e arquivos.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Qualidade | Fixação em 320k para garantir fidelidade DJ. | `converter.py:45` | 🟢 |
| Precisão | Uso de cálculo de floating point para o ratio. | `converter.py:38` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Conversão com Sucesso e Stretch
```gherkin
Dado um WAV de 128 BPM e Target de 126 BPM
Quando o Converter é executado
Então o comando FFmpeg deve incluir "-filter:a atempo=0.984"
E o arquivo MP3 deve ser salvo em "music/126/..."
```

### Cenário 2: Faixa de Alta Velocidade (Double Tempo)
```gherkin
Dado um WAV de 70 BPM e Target de 140 BPM
Quando a conversão ocorre
Então a velocidade do áudio deve ser dobrada (atempo=2.0)
E o pitch musical não deve ser alterado.
```

## Cenários de Borda
1. **Ratio Extremo (< 0.5 ou > 2.0):** O filtro `atempo` falha se o valor for fora desta faixa. O sistema deve encadear filtros (ex: `atempo=0.4` -> falha; solução: `atempo=0.8,atempo=0.5`). 🔴 (Atualmente lacuna identificada na análise técnica).
2. **Nomes de Arquivo com Aspas:** O uso de `subprocess` com strings concatenadas pode ser vulnerável ou falhar se o `safe_title` não for rigoroso. 🟡

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Conversão para MP3 | Must | Produto final do sistema. |
| Time-Stretching (atempo) | Must | Funcionalidade central para normalização rítmica. |
| Organização de Pastas | Should | Facilita a gestão da biblioteca, mas não afeta o áudio. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/converter.py` | `Converter` | 🟢 |
| `beatforge/converter.py` | `convert` | 🟢 |
