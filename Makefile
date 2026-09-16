# Shortcuts so you type `make test` instead of remembering long commands.
IMAGE ?= flask-docker-ci
PORT  ?= 8000

.PHONY: install test lint build run stop clean

install:          ## install dependencies locally
	python3 -m venv .venv && ./.venv/bin/pip install -r requirements-dev.txt

test:             ## run the test suite
	./.venv/bin/pytest -v

lint:             ## check code style
	./.venv/bin/ruff check .

build:            ## build the docker image
	docker build -t $(IMAGE):local .

run: build        ## build then run the container
	docker run -d --rm --name $(IMAGE) -p $(PORT):8000 $(IMAGE):local
	@echo "-> http://localhost:$(PORT)"

stop:             ## stop the running container
	-docker stop $(IMAGE)

clean:            ## remove local build artifacts
	rm -rf .venv .pytest_cache .ruff_cache __pycache__ tests/__pycache__
