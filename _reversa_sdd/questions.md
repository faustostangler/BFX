# Questões de Validação — BFX

> Gerado pelo Reviewer em 2026-04-30
> Por favor, preencha o campo **Resposta** para cada item.

## 🔴 Lacunas Críticas

### 1. Localização dos Modelos de Deep Learning
**Componente:** `sdd/feature-extractor.md`
**Contexto:** O código em `beatforge/essentia_features.py:150-151` utiliza caminhos de exemplo: `"/path/to/vggish_model.pb"`.
**Pergunta:** Existe um local padrão no repositório ou no container onde esses arquivos residem? Ou eles devem ser baixados dinamicamente via Makefile?
**Resposta:** não sei responder, utilize o caminho mais simples. 

---

### 2. Timeouts de Subprocesso
**Componente:** `sdd/orchestrator.md` / `sdd/downloader.md`
**Contexto:** Chamadas ao `yt-dlp` e `ffmpeg` podem demorar ou travar dependendo da rede ou do arquivo. Atualmente não há `timeout` definido no `subprocess.run`.
**Pergunta:** Devemos especificar um tempo máximo de espera por faixa (ex: 5 minutos para download, 2 minutos para análise)?
**Resposta:** sim, sugestão aceita. 5 minutos para download, 2 minutos para análise. 

---

### 3. Recuperação de Banco de Dados
**Componente:** `sdd/persistence.md`
**Contexto:** O SQLite é robusto, mas sujeito a corrupção em desligamentos súbitos.
**Pergunta:** Se o banco `playlist.db` estiver corrompido, o sistema deve tentar deletá-lo e recomeçar do zero automaticamente ou deve apenas falhar com um erro claro para intervenção humana?
**Resposta:** deletar e recomeçar do zero automaticamente.

---

## 🟡 Observações Moderadas

### 4. Limite de Time-Stretch
**Componente:** `sdd/audio-converter.md`
**Contexto:** O filtro `atempo` do FFmpeg suporta apenas ratios entre 0.5 e 2.0.
**Pergunta:** Caso uma música exija um ajuste fora desse limite (ex: 150 BPM para 70 BPM), o sistema deve aplicar filtros em cascata (suportado pelo FFmpeg mas complexo) ou apenas ignorar a faixa?
**Resposta:** aplicar filtros em cascata. 
