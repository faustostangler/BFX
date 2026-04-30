# Matriz de Permissões e Acesso — BFX

> Gerado pelo Detective em 2026-04-30

O sistema BFX é projetado como uma ferramenta de **CLI/Worker de Uso Único** e não possui uma camada de autenticação de usuários (RBAC/ACL) embutida no código.

## 👥 Papéis (Roles)

| Papel | Descrição | Escopo |
| :--- | :--- | :--- |
| **System Operator** | Usuário que executa o `main.py` ou `make local-run`. | Acesso total ao sistema de arquivos e banco SQLite. |
| **Container Runtime** | O processo dentro do Docker. | Restrito aos volumes montados (`/app/music`, `/app/data`). |

## 🛡️ Segurança e Restrições

- **Acesso ao Banco:** O banco de dados `playlist.db` é um arquivo SQLite local. O acesso é controlado pelas permissões do sistema operacional.
- **Integrações Externas:** O acesso ao YouTube é feito via `yt-dlp`. Não há chaves de API armazenadas (exceto se configuradas globalmente no ambiente), operando em modo anônimo por padrão.
- **Segurança de Código:** O uso de `subprocess.run` para FFmpeg utiliza strings sanitizadas via `make_safe_title` (que remove caracteres especiais e aspas), mitigando riscos de Command Injection.

## 🔴 Lacunas
- Não há limite de taxa (Rate Limit) implementado para as chamadas ao YouTube, o que pode levar a banimentos temporários de IP.
