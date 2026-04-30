# User Story: Pipeline de Processamento Rítmico

> Gerado pelo Writer em 2026-04-30

## 📝 Descrição
Como um **DJ / Produtor**, eu quero que o sistema processe as faixas selecionadas, detectando seu BPM exato e ajustando-as para velocidades padronizadas (buckets), para que minha biblioteca esteja sempre pronta para mixagem imediata (beatmatch perfeito).

## 🗺️ Fluxo do Usuário
1. O sistema inicia o processamento de uma faixa selecionada.
2. O áudio é baixado e convertido para WAV para máxima fidelidade na análise.
3. O sistema analisa a estrutura rítmica e extrai centenas de características (features) acústicas.
4. O sistema decide o BPM-alvo (ex: 120, 124, 128) com base no BPM original detectado.
5. O sistema aplica o ajuste de tempo (time-stretch) sem alterar o tom da música.
6. O sistema entrega o MP3 final em uma pasta organizada e uma amostra de áudio de 15s.

## ✅ Critérios de Aceitação

### Cenário 1: Normalização Rítmica (Beatmatching)
- **Dado** uma música baixada com 123 BPM.
- **Quando** o sistema processa a normalização.
- **Então** ele deve calcular o ratio de ajuste para atingir o target de 124 BPM.
- **E** o arquivo final deve ser salvo em `music/124/<Gênero>/`.
- **E** o áudio não deve apresentar distorção tonal (pitch shift).

### Cenário 2: Análise Acústica Profunda
- **Dado** o processamento de uma nova faixa.
- **Quando** a extração de features é concluída.
- **Então** o banco de dados deve ser atualizado com MFCCs, Key (Tom) e Deep Embeddings (VGGish).
- **E** esses dados devem estar disponíveis para futuras buscas por similaridade sonora.

### Cenário 3: Economia de Recursos (Cleanup)
- **Dado** que a conversão para MP3 foi finalizada com sucesso.
- **Quando** o pipeline encerra para aquela faixa.
- **Então** o arquivo WAV original (pesado) deve ser excluído automaticamente do disco.

## 🔴 Cenários de Borda
- **BPM Indetectável:** Se o áudio for ruidoso ou experimental, o sistema deve registrar o BPM detectado com menor confiança, mas ainda assim completar o pipeline de conversão.
- **Erro no FFmpeg durante o Stretch:** Se o filtro `atempo` falhar (ex: áudio muito curto ou ratio inválido), o sistema deve abortar a criação do MP3 daquela faixa e logar o erro, preservando a integridade da biblioteca.
