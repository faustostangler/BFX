# BPMAnalyzer

## Visão Geral
Componente de análise rítmica que detecta a pulsação do áudio (BPM) e decide o "bucket" de destino para a normalização da biblioteca.

## Responsabilidades
- Detectar o BPM predominante de um arquivo WAV usando múltiplas engines (Essentia/Librosa). 🟢
- Normalizar BPMs extremos (muito lentos ou muito rápidos) usando lógica de oitavas. 🟢
- Escolher o BPM alvo (Target BPM) baseado em uma grade rítmica pré-definida. 🟢

## Interface
- **Entrada:** Caminho do arquivo WAV.
- **Saída:** BPM original detectado (float) e Target BPM selecionado (int).

## Regras de Negócio
- **Dual Engine Logic:** Tenta extração via `Essentia` (RhythmExtractor2013). Se falhar ou não houver confiança, usa `Librosa` (tempo) como fallback. 🟢
- **Oitava Normalization:** 
    - Se BPM < 45, multiplica por 2 (Half-time correction). 🟢
    - Se BPM > 210, divide por 2 (Double-time correction). 🟢
- **Bucket Selection:**
    - Divide o espectro em intervalos de 20 BPM (ex: 105-125, 125-145). 🟢
    - O **Target** é o início do intervalo + 15 (ex: balde 105-125 -> Target 120). 🟢

## Fluxo Principal
1. Receber arquivo WAV.
2. Tentar extração via Essentia.
3. Se falhar, executar extração via Librosa.
4. Aplicar regra de normalização de oitavas.
5. Calcular a qual faixa de 20 BPM o valor pertence.
6. Retornar o valor do Target BPM fixo daquela faixa.

## Fluxos Alternativos
- **Silêncio ou Áudio não rítmico:** O analyzer pode retornar BPM inconsistente. O sistema assume o valor detectado e prossegue, podendo gerar resultados imprevisíveis. 🔴

## Dependências
- `essentia` (Python lib) — Engine primária de análise rítmica.
- `librosa` (Python lib) — Engine secundária/fallback.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Precisão | Uso do método `multifeature` do Essentia para maior acurácia. | `bpm.py:59` | 🟢 |
| Resiliência | Fallback para Librosa em caso de erro na engine principal. | `bpm.py:65` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Detecção e Bucketização Padrão
```gherkin
Dado um arquivo WAV com rítmo de 118 BPM
Quando o BPMAnalyzer processa o arquivo
Então o BPM original deve ser ~118.0
E o Target BPM selecionado deve ser 120 (balde 105-125).
```

### Cenário 2: Correção de Oitava (Lento)
```gherkin
Dado um arquivo WAV com rítmo de 40 BPM
Quando o BPMAnalyzer processa o arquivo
Então o valor deve ser normalizado para 80 BPM
E o Target BPM deve ser calculado a partir de 80.
```

## Cenários de Borda
1. **BPM em 125 (Limite de Balde):** O sistema deve decidir de forma determinística se pertence ao balde inferior ou superior (atual: `start < bpm <= end`). 🟢
2. **Áudio muito curto (< 10s):** A confiança da detecção cai drasticamente. O sistema não possui validação de duração mínima 🔴.

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Detecção de BPM | Must | Base para a organização da biblioteca e para o time-stretching. |
| Fallback Engine | Should | Garante que o processo continue mesmo em falhas de bibliotecas complexas. |
| Normalização de Oitavas | Must | Essencial para DJs que operam em faixas rítmicas padrão. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/bpm.py` | `BPMAnalyzer` | 🟢 |
| `beatforge/bpm.py` | `_normalize_bpm` | 🟢 |
| `beatforge/bpm.py` | `choose_target` | 🟢 |
