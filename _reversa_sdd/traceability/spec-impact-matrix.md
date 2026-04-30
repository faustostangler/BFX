# Matriz de Impacto de Especificações (Spec Impact Matrix) — BFX

Esta matriz mapeia o impacto de mudanças em um componente sobre os outros e sobre a documentação gerada.

| Componente | PlaylistManager | Downloader | BPMAnalyzer | FeatureExtractor | Converter | Sampler | Persistence |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **PlaylistManager** | - | 🔴 High | ⚪ None | ⚪ None | 🟡 Med | ⚪ None | 🔴 High |
| **Downloader** | ⚪ None | - | 🔴 High | 🔴 High | 🔴 High | ⚪ None | 🟡 Med |
| **BPMAnalyzer** | ⚪ None | ⚪ None | - | ⚪ None | 🔴 High | ⚪ None | 🟡 Med |
| **FeatureExtractor**| ⚪ None | ⚪ None | ⚪ None | - | ⚪ None | ⚪ None | 🔴 High |
| **Converter** | ⚪ None | ⚪ None | ⚪ None | ⚪ None | - | 🔴 High | 🟡 Med |
| **Sampler** | ⚪ None | ⚪ None | ⚪ None | ⚪ None | ⚪ None | - | ⚪ None |
| **Persistence** | 🔴 High | 🟡 Med | 🟡 Med | 🔴 High | 🟡 Med | ⚪ None | - |

### Legenda de Impacto:
- 🔴 **High:** Mudanças na API ou estrutura de dados quebram obrigatoriamente o componente dependente.
- 🟡 **Med:** Mudanças podem exigir ajustes de configuração ou lógica de processamento.
- ⚪ **None:** Componentes independentes.

### Rastreabilidade de Documentação:
- Mudanças no **Persistence** impactam: `data-dictionary.md`, `erd-complete.md`.
- Mudanças no **PlaylistManager** impactam: `domain.md` (regras de scoring).
- Mudanças no **BPMAnalyzer** impactam: `flowcharts/bpm.md`, `adrs/0004-bpm-bucketization.md`.
