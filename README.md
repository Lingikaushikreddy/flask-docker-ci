# Project 1 — Flask API, Dockerized, with a CI/CD Pipeline

[![CI](https://github.com/Lingikaushikreddy/flask-docker-ci/actions/workflows/ci.yml/badge.svg)](https://github.com/Lingikaushikreddy/flask-docker-ci/actions/workflows/ci.yml)

A small Python API that is **linted, tested, containerized, smoke-tested and published as a Docker image — automatically, on every push.**

The app itself is deliberately boring. The interesting part is everything *around* it.

---

## What this demonstrates

| Skill | Where to look |
|---|---|
| Containerization | `Dockerfile` — multi-stage, non-root, healthcheck |
| Automated testing | `tests/test_app.py` — 7 tests |
| Linting / code quality | `pyproject.toml` — ruff |
| CI/CD | `.github/workflows/ci.yml` |
| Container registry | Image published to GitHub Container Registry (GHCR) |
| Config via environment | `APP_VERSION` env var |

---

## The API

| Method | Route | What it does |
|---|---|---|
| `GET` | `/` | Service info |
| `GET` | `/health` | Liveness probe — used by Docker's `HEALTHCHECK` |
| `GET` | `/api/greet/<name>` | `{"greeting": "Hello, <name>!"}` |
| `POST` | `/api/sum` | `{"numbers":[1,2,3]}` → `{"sum":6,"count":3}` |

Bad input returns `400`, unknown routes return `404` — both as JSON, both tested.

---

## Run it

### With Docker (the point of the project)

```bash
docker build -t flask-docker-ci:local .
docker run -d --rm --name api -p 8080:8000 flask-docker-ci:local

curl http://127.0.0.1:8080/health
curl http://127.0.0.1:8080/api/greet/Kaushik
curl -X POST http://127.0.0.1:8080/api/sum \
     -H 'Content-Type: application/json' \
     -d '{"numbers":[1,2,3,4,5]}'

docker stop api
```

> **Note:** we map host port **8080** → container port 8000. If port 8080 is busy on
> your machine, pick another: `-p 9000:8000`. The number on the *right* never changes —
> that's the port *inside* the container.

### Pull the published image instead of building

```bash
docker pull ghcr.io/lingikaushikreddy/flask-docker-ci:latest
docker run -d --rm -p 8080:8000 ghcr.io/lingikaushikreddy/flask-docker-ci:latest
```

### Without Docker

```bash
make install   # creates .venv and installs everything
make test      # run the tests
make lint      # check code style
```

---

## How the Dockerfile works (read this — it's the lesson)

It's a **multi-stage build**: two images, but only the second one ships.

```
Stage 1 "builder"            Stage 2 "runtime"
┌────────────────────┐       ┌────────────────────┐
│ python:3.12-slim   │       │ python:3.12-slim   │
│ pip install ...    │  ──►  │ COPY /opt/venv     │  ← only the venv crosses over
│ (pip cache, junk)  │       │ COPY app.py        │
└────────────────────┘       │ USER appuser       │
   thrown away               └────────────────────┘
                                 241 MB shipped
```

Four things worth copying into your own projects:

1. **`COPY requirements.txt` before `COPY app.py`.** Docker caches layers. Dependencies
   change rarely, your code changes constantly — so install deps in an earlier layer and
   editing code won't re-download Flask every single build.
2. **`USER appuser`.** Containers run as root by default. If someone breaks out of your
   app, root is a much worse day than `appuser`.
3. **`HEALTHCHECK`.** Lets Docker tell the difference between "the process is running"
   and "the app actually works". Run `docker ps` and you'll literally see `(healthy)`.
4. **`gunicorn`, not `flask run`.** The Flask dev server is single-threaded and prints a
   warning telling you not to use it in production. Believe the warning.

---

## How the CI pipeline works

Every push to `main` triggers `.github/workflows/ci.yml`:

```
push to main
     │
     ├─ Job 1: test ─────────────────────────────┐
     │    ruff check .          (style)           │
     │    pytest -v             (7 tests)         │
     │                                            │
     └─ Job 2: docker  ◄── only runs if Job 1 passed
          docker build
          run the container + curl it   ← smoke test: does it REALLY work?
          push to ghcr.io               ← only on main, not on pull requests
```

Details that matter:

- **`needs: test`** — the image is never built from code that failed its tests.
- **The smoke test** catches what unit tests can't: a broken `CMD`, a missing file in the
  image, a port that isn't listening. The tests can pass while the *container* is broken.
- **`if: github.event_name == 'push'`** — pull requests build and test but don't publish.
  Nothing from an unmerged PR reaches the registry.
- **`secrets.GITHUB_TOKEN`** is created by GitHub automatically for each run. No password
  is ever stored in this repo. This is the habit to build: **credentials never live in git.**

---

## Things I got wrong while building this (and what fixed them)

Keeping these here because the debugging *is* the learning:

- **`ModuleNotFoundError: No module named 'app'`** — pytest doesn't put your project root
  on the import path. Fixed with `pythonpath = ["."]` in `pyproject.toml`.
- **`curl: (56) Connection reset by peer`** — the container was still booting. Docker
  accepts the TCP connection immediately and *then* resets it, so `--retry-connrefused`
  doesn't help; it only retries refusals. That's why the CI smoke test uses a real retry
  loop instead.
- **Port 8000 already in use** — another app on my machine held it, so requests silently
  went to the wrong service. Lesson: when something "doesn't work", check
  `lsof -nP -iTCP:8000 -sTCP:LISTEN` before blaming your code.

---

## Layout

```
flask-docker-ci/
├── app.py                    # the API
├── tests/test_app.py         # 7 pytest tests
├── Dockerfile                # multi-stage, non-root, healthcheck
├── .dockerignore             # keeps tests/secrets out of the image
├── requirements.txt          # runtime deps (pinned)
├── requirements-dev.txt      # test + lint deps
├── pyproject.toml            # ruff + pytest config
├── Makefile                  # make install / test / lint / build / run
└── .github/workflows/ci.yml  # the pipeline
```

---

## What to try next

- Break a test on purpose, push, and watch CI go red. Then fix it and watch it go green.
- Add a `/api/multiply` endpoint — test first, then code.
- Add a `docker-compose.yml` so `docker compose up` replaces the long `docker run`.
- See **Project 2** for the multi-container version of all this.
