# Dockerfile

# Use a imagem oficial do Python slim como base
FROM python:3.12-slim AS base

# Configurações de ambiente para Python e uv
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Instala dependências de sistema (ffmpeg para áudio, nodejs para yt-dlp, curl para uv)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    nodejs \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Instala o uv (astral-sh)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Define o diretório de trabalho
WORKDIR /app

# Instala dependências antes do código para aproveitar o cache de camadas
COPY requirements.txt .
RUN uv pip install --system -r requirements.txt

# Copia o código fonte e arquivos de configuração
COPY . .

# Cria os diretórios para volumes
RUN mkdir -p /app/music /app/data

# Volume de persistência para o banco SQLite e músicas
VOLUME ["/app/music", "/app/data"]

# Entrypoint padrão (executa o pipeline)
CMD ["python", "main.py"]
