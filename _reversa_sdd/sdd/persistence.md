# Persistence Layer

## Visão Geral
Camada de dados responsável por gerir a persistência de metadados, análise e estado das faixas musicais usando um banco de dados relacional leve (SQLite).

## Responsabilidades
- Inicializar e gerenciar o esquema do banco de dados (`playlist.db`). 🟢
- Realizar operações de Upsert (Insert or Replace) para faixas processadas. 🟢
- Carregar o inventário completo de faixas para filtragem e consulta. 🟢
- Serializar e desserializar objetos complexos (listas, dicionários) para armazenamento em colunas de texto (JSON). 🟢
- Gerenciar migrações manuais simples (ex: adição de colunas). 🟢

## Interface
- **Entrada:** Objetos `TrackDTO` ou listas de objetos.
- **Saída:** Objetos `TrackDTO` reconstruídos a partir do banco; Conjunto de URLs processadas.

## Regras de Negócio
- **Single Source of Truth (SSOT):** O arquivo `playlist.db` é o repositório central de toda a inteligência extraída do YouTube e das análises DSP. 🟢
- **Auto-Migration:** Ao iniciar, o componente checa se colunas obrigatórias (ex: `genre`) existem e as cria via `ALTER TABLE` se necessário. 🟢
- **JSON Serialization:** Campos como `timbral_mfcc_mean` e `deep_embeds_vggish` são convertidos para string JSON antes da inserção e voltados para listas Python na leitura. 🟢
- **Atomicidade de URL:** A URL do YouTube é a Chave Primária única; duplicatas são substituídas pela versão mais recente (Update). 🟢

## Fluxo Principal
1. Inicializar conexão SQLite.
2. Executar `ensure_schema` para validar tabelas e colunas.
3. Disponibilizar métodos `save_track_list`, `load_all_tracks` e `get_processed_urls`.
4. Fechar conexão graciosamente ao encerrar o sistema.

## Fluxos Alternativos
- **Banco de dados corrompido:** O SQLite lançará erro de I/O; o componente deve capturar e sugerir a recriação do banco (lacuna 🔴).
- **Incompatibilidade de Versão:** Se o esquema mudar drasticamente, as migrações manuais podem falhar. 🟡

## Dependências
- `sqlite3` (Python standard lib) — Motor de banco de dados.
- `json` (Python standard lib) — Para serialização de objetos complexos.
- `dataclasses` / `TrackDTO` — Para mapeamento objeto-relacional simplificado.

## Requisitos Não Funcionais

| Tipo | Requisito inferido | Evidência no código | Confiança |
| :--- | :--- | :--- | :---: |
| Simplicidade | Uso de Zero-Config database (SQLite). | `persistence.py:20` | 🟢 |
| Resiliência | Auto-recovery: Deletar e recriar banco automaticamente em caso de corrupção. | [Validação Humana] | 🟢 |
| Evolução | Mecanismo de migração manual para evolução de esquema. | `persistence.py:35` | 🟢 |

## Critérios de Aceitação

### Cenário 1: Persistência de Faixa com JSON
```gherkin
Dado um TrackDTO com uma lista de 13 MFCCs
Quando save_track_list é executado
Então o banco de dados deve conter a string JSON dos MFCCs na coluna correspondente
E ao carregar via load_all_tracks, o campo MFCC deve ser uma lista de números novamente.
```

### Cenário 2: Prevenção de Duplicatas
```gherkin
Dado que a URL "youtube.com/abc" já existe no banco
Quando salvamos um novo TrackDTO com a mesma URL "youtube.com/abc"
Então o registro antigo deve ser atualizado com os novos dados
E o número total de registros no banco não deve aumentar.
```

## Cenários de Borda
1. **Concurrency (Locking):** O SQLite possui travas de escrita (`database is locked`) se múltiplos processos tentarem escrever simultaneamente. O sistema atual é síncrono e evita isso, mas uma evolução para paralelo exigiria tratamento de retentativa 🟡.

## Prioridade

| Requisito | MoSCoW | Justificativa |
| :--- | :---: | :--- |
| Upsert de Faixas | Must | Garante que o trabalho de análise não seja perdido. |
| Auto-Migration | Should | Facilita atualizações do software sem intervenção manual no banco. |
| JSON Serialization | Must | Necessário para armazenar features acústicas ricas (vetores). |

## Rastreabilidade de Código

| Arquivo | Função / Classe | Cobertura |
| :--- | :--- | :---: |
| `beatforge/persistence.py` | `Persistence` | 🟢 |
| `beatforge/persistence.py` | `ensure_schema` | 🟢 |
| `beatforge/persistence.py` | `save_track_list` | 🟢 |
