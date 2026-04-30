# EssentiaFeatureExtractor

## Visão Geral
Componente de extração massiva de características musicais (Music Information Retrieval - MIR). Utiliza processamento digital de sinais (DSP) e Deep Learning para gerar uma assinatura acústica detalhada de cada faixa.

## Responsabilidades
- Extrair características timbrais (MFCC). 🟢
- Analisar características espectrais (Centroid, Rolloff, Flatness, Flux, ZCR). 🟢
- Detectar tonalidade (Key) e escala (Major/Minor). 🟢
- Extrair características dinâmicas (Loudness, Energy, RMS). 🟢
- Gerar Deep Embeddings de 128 dimensões usando o modelo VGGish (TensorFlow). 🟢
- Agregar estatísticas de frames (média e desvio padrão). 🟢

## Interface
- **Entrada:** Caminho do arquivo WAV.
- **Saída:** Dicionário aninhado com metadados técnicos e vetores numéricos.

## Regras de Negócio
- **Import Dinâmico:** Carrega algoritmos Essentia opcionalmente para evitar falhas se a instalação local do Essentia não for completa. 🟢
- **Processamento por Frames:** Janelas de 1024 frames com hop de 512. Usa janelamento de Hann e espectro de magnitude. 🟢
- **VGGish Path:** Localizado em `./models/vggish_model.pb` (ou configurável via env). 🟢
- **Estatísticas:** Transforma séries temporais de frames em escalares representativos (média/std) para facilitar a persistência e busca. 🟢

## Fluxo Principal
1. Carregar áudio via `MonoLoader`.
2. Executar extratores globais (Rhythm, Key, Onsets).
3. Iniciar `FrameGenerator`.
4. Para cada frame:
    a. Aplicar Janelamento.
    b. Calcular Espectro.
    c. Extrair MFCC, Centroid, ZCR, etc.
5. Agregar médias e desvios padrão.
6. Se TensorFlow/VGGish estiver disponível:
    a. Resample para 16kHz.
    b. Processar patches.
    c. Gerar embeddings de 128 dimensões.
7. Retornar dicionário consolidado.

## Fluxos Alternativos
- **Algoritmo Essentia Faltante:** O componente captura o `ImportError` ou `AttributeError`, define o extrator como `None` e retorna um campo vazio no dicionário final sem interromper a execução. 🟢
- **Erro no Modelo VGGish:** Captura exceções de carregamento de arquivo `.pb` ou `.json` e desativa silenciosamente a extração de deep embeds. 🟢

## Dependências
- `essentia` — Engine DSP.
- `tensorflow` — Para inferência do modelo VGGish.
- `numpy` — Manipulação de vetores e agregação estatística.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Escalabilidade | Processamento por frames (Generator) para evitar estouro de memória em arquivos longos. | `essentia_features.py:223` | 🟢 |
| Extensibilidade | Estrutura de try/except para algoritmos opcionais. | `essentia_features.py:25-74` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Extração Completa com VGGish
```gherkin
Dado um arquivo WAV e o modelo VGGish instalado
Quando o extract_all é executado
Então o retorno deve conter seções "timbral", "spectral", "dynamics", "chroma" e "deep_embeds"
E a seção "vggish" deve conter uma lista de 128 floats.
```

### Cenário 2: Fallback sem Essentia Completo
```gherkin
Dado um ambiente sem o algoritmo "SpectralContrast"
Quando a extração é realizada
Então o sistema deve completar a tarefa com sucesso
E o campo "contrast_mean" deve ser uma lista vazia.
```

## Cenários de Borda
1. **Paths de Modelos Inválidos:** Os paths para `vggish_model.pb` estão hardcoded em `essentia_features.py:150-151`. Se o arquivo não existir, o sistema falhará silenciosamente na extração de embeddings 🔴.
2. **Áudio Mono vs Stereo:** O `MonoLoader` força o áudio para Mono; informações de pan ou largura estéreo são perdidas na análise 🟢.

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Extração DSP Básica | Must | Essencial para indexação musical e organização. |
| Deep Embeddings (VGGish) | Should | Diferencial tecnológico para busca por similaridade futura. |
| Detecção de Key/Scale | Should | Importante para Harmonic Mixing de DJs. |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/essentia_features.py` | `EssentiaFeatureExtractor` | 🟢 |
| `beatforge/essentia_features.py` | `extract_all` | 🟢 |
