.PHONY: dev dev_install backend frontend test

dev:
	./run.sh

NVM_DIR ?= $(HOME)/.nvm
NODE_VERSION := $(shell cat .nvmrc)

dev_install:
	@echo "--- Checking uv ---"
	command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@echo "--- Checking nvm ---"
	[ -s "$(NVM_DIR)/nvm.sh" ] || (echo "Installing nvm..." && curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash)
	@echo "--- Installing Node via nvm ---"
	bash -c 'source "$(NVM_DIR)/nvm.sh"; nvm install $(NODE_VERSION) && nvm use $(NODE_VERSION)'
	@echo "--- Installing frontend dependencies ---"
	bash -c 'source "$(NVM_DIR)/nvm.sh"; nvm use $(NODE_VERSION) && cd frontend && npm install'
	@echo "--- Installing backend dependencies ---"
	cd backend && uv sync --extra dev

backend:
	./run.sh backend

frontend:
	./run.sh frontend

test:
	./run.sh test
