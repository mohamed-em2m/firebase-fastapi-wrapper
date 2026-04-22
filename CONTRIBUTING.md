# Contributing to firebase-fastapi-wrapper

Thank you for taking the time to contribute! 🎉

---

## Development Setup

```bash
# 1. Clone the repository
git clone https://github.com/Mohamed-Em2m/FastApi-with-Firebase-functions.git
cd FastApi-with-Firebase-functions

# 2. Install uv (if not already installed)
curl -Lssf https://astral.sh/uv/install.sh | sh

# 3. Create a virtual environment and install all dependencies
uv sync --extra dev

# 4. Install pre-commit hooks
uv run pre-commit install
```

---

## Running Tests

```bash
# Run the full test suite
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ -v --cov=firebase_fastapi_wrapper --cov-report=term-missing
```

All tests should pass before you open a PR.

---

## Code Style

We use [Ruff](https://docs.astral.sh/ruff/) for linting and formatting:

```bash
# Check for lint issues
uv run ruff check .

# Auto-fix
uv run ruff check --fix .

# Format
uv run ruff format .
```

Pre-commit hooks run these automatically before every commit.

---

## Commit Messages

This project uses [Conventional Commits](https://www.conventionalcommits.org/) with [Gitmoji](https://gitmoji.dev/):

```
✨ feat: add cors_origins parameter
🐛 fix: remove leading space from wrapper filename
📝 docs: rewrite README with local dev section
🔧 chore: upgrade python-app.yml to uv + ruff
♻️ refactor: extract _inject_cors helper
✅ test: add DELETE and CORS tests
```

Commit messages are validated by the `commitizen` pre-commit hook.

---

## Opening a Pull Request

1. Fork the repo and create a feature branch from `main`.
2. Make your changes, add tests, and ensure all checks pass.
3. Push your branch and open a PR against `main`.
4. Fill in the PR template and reference any related issues.

---

## Reporting Issues

Open an issue at [GitHub Issues](https://github.com/Mohamed-Em2m/FastApi-with-Firebase-functions/issues)
and include:
- Your Python version (`python --version`)
- Your installed package version (`pip show firebase-fastapi-wrapper`)
- A minimal reproducible example
