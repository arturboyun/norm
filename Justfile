install:
    uv lock --upgrade
    uv sync --all-extras --frozen

check:
    uv run ruff check src tests --fix
    uv run mypy src tests

test:
    uv run pytest --cov=src --cov-report=xml --cov-report=html
