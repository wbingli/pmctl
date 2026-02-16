# AGENTS.md

Instructions for AI agents working on this project.

## Project Overview

`pmctl` is a Python CLI tool for managing Postman collections, environments, and workspaces. It wraps the [Postman API](https://www.postman.com/postman/postman-public-workspace/documentation/12946884/postman-api) and is built with Typer + Rich.

## Project Structure

```
src/pmctl/
  __init__.py   # Package version (__version__)
  cli.py        # All CLI commands (Typer app)
  api.py        # Postman API client (httpx)
  config.py     # Profile/config management (~/.config/pmctl/config.toml)
pyproject.toml  # Project metadata, version, dependencies (hatchling build)
uv.lock         # Locked dependencies
```

## Key Files

- **Version** is defined in two places — keep them in sync:
  - `pyproject.toml` → `version = "x.y.z"`
  - `src/pmctl/__init__.py` → `__version__ = "x.y.z"`
- **Entry point**: `pmctl.cli:app` (Typer app)

## Development

### Setup

```bash
uv sync          # Install dependencies from lockfile
uv pip install -e .  # Editable install for local development
```

### Linting

```bash
uv run ruff check src/
uv run ruff format src/
```

Ruff config: Python 3.11 target, 100 char line length (see `pyproject.toml`).

## Build & Publish

### 1. Bump version

Update version in **both** files:
- `pyproject.toml` → `version`
- `src/pmctl/__init__.py` → `__version__`

### 2. Build

```bash
uv build
```

Produces `dist/pmctl-<version>.tar.gz` and `dist/pmctl-<version>-py3-none-any.whl`.

### 3. Publish

PyPI credentials are stored in `~/.pypirc` with token auth. Use `twine` to upload:

```bash
# Test PyPI first
twine upload --repository testpypi dist/pmctl-<version>*

# Then production PyPI
twine upload dist/pmctl-<version>*
```

- Test PyPI: https://test.pypi.org/project/pmctl/
- Prod PyPI: https://pypi.org/project/pmctl/

### 4. Commit convention

After bumping version and publishing, commit with a message like:
```
Bump to v<version> and <summary of changes>
```

Always push to `main` after publishing.

## CLI Architecture

- Commands are organized as Typer sub-apps: `profile`, `workspaces`, `collections`, `environments`, `completion`
- All output uses Rich (`Console`, `Table`, `Tree`)
- Every command that calls the API accepts `--profile`/`-p` to select which Postman account to use
- List commands respect the profile's default workspace; use `--all`/`-a` to override
- The `show` commands support lookup by name or ID where practical (environments resolve name via workspace list)

## Postman API

- Base URL: `https://api.getpostman.com`
- Auth: `X-API-Key` header with the profile's API key
- Client is in `api.py` using `httpx` with context manager pattern
- Rate limits apply — avoid unnecessary API calls
