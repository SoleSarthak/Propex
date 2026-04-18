# Contributing to Propex

## Development Setup
1.  **Docker**: Ensure Docker Desktop is running.
2.  **Environment**: Copy `.env.example` to `.env`.
3.  **Setup Script**: Run `./scripts/setup-dev.ps1` (Windows) or `make setup`.

## Monorepo Structure
- `apps/web-dashboard`: React (Vite) frontend.
- `libs/python-shared`: Core Pydantic models, DB sessions, and Kafka helpers.
- `libs/scoring-engine`: Vulnerability scoring logic.
- `services/`: Microservices (CVE Ingestion, Resolvers, etc.).

## Coding Standards
- **Python**:
  - Use `black` for formatting.
  - Use `flake8` for linting.
  - Use `mypy` for type checking.
  - Follow PEP 8.
- **TypeScript**:
  - Use `prettier` and `eslint`.
  - Use Functional Components with Hooks.

## Pull Request Process
1.  Create a branch from `main`.
2.  Ensure all tests pass (`make test`).
3.  Ensure linters pass (`make lint`).
4.  Submit PR and wait for review.

## Branch Naming
- `feat/...` for new features.
- `fix/...` for bug fixes.
- `docs/...` for documentation.
