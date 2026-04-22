# Makefile para BeatForge (BFX)

.PHONY: up down restart logs shell build clean local-run help

# --- Variáveis ---
DOCKER_COMPOSE = docker compose
PYTHON = python
UV = uv

help:
	@echo "Comandos disponíveis:"
	@echo "  make up          - Inicia o container em background"
	@echo "  make down        - Para os containers e remove a rede"
	@echo "  make restart     - Reinicia os containers"
	@echo "  make logs        - Visualiza os logs em tempo real"
	@echo "  make build       - Reconstrói a imagem Docker"
	@echo "  make shell       - Abre um terminal dentro do container"
	@echo "  make local-run   - Roda o pipeline localmente (usando uv)"
	@echo "  make clean       - Remove arquivos temporários e caches"

# --- Docker Commands ---

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down

restart:
	$(DOCKER_COMPOSE) restart

logs:
	$(DOCKER_COMPOSE) logs -f

build:
	$(DOCKER_COMPOSE) build --no-cache

shell:
	$(DOCKER_COMPOSE) exec beatforge /bin/bash

# --- Local Development ---

local-run:
	$(UV) run main.py

# --- Maintenance ---

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".uv" -exec rm -rf {} +
