# Repository Guidelines

## Project Structure & Module Organization
The code lives under the `ppl/` package.  Core modules are:
* `ppl/models/` – data structures such as contacts, filters, and graphs.
* `ppl/filters/` – reusable filter implementations.
* `ppl/serializers/` – import/export helpers (markdown, vCard, yaml).
* `ppl/cli.py` – entry‑point for the command‑line tool.

Tests reside in the top‑level `tests/` directory mirroring the package layout.  Example data and assets are in `examples/` and `tmp/`.

## Build, Test, and Development Commands
* `make` – runs the default target (`make test`).
* `make test` – executes the full pytest suite.
* `make lint` – runs `ruff` (if installed) to check style.
* `python -m ppl.cli <args>` – runs the CLI locally.

These commands assume a standard Python virtual environment.

## Coding Style & Naming Conventions
* Use 4‑space indentation; no tabs.
* Follow **PEP 8** – line length ≤ 88, snake_case for variables/functions, PascalCase for classes.
* Type hints are encouraged for public APIs.
* Run `ruff` or `black` (configured via `pyproject.toml`) before committing.

## Testing Guidelines
* Tests use **pytest**.  Each test file mirrors the module it tests (`test_<module>.py`).
* Name test functions descriptively, e.g. `def test_filter_by_gender():`.
* Run the suite with `make test` or `pytest -q`.
* Aim for ≥ 80 % coverage; view coverage with `pytest --cov=ppl`.

## Commit & Pull Request Guidelines
* Commit messages follow the conventional format:
  `type(scope): short summary`
  where `type` is one of `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.
* Include a brief description of the change and reference any related issue (`#123`).
* Pull requests must contain:
  - A clear description of the purpose.
  - Links to related issues.
  - Screenshots or example output when UI/CLI changes affect behavior.
  - Confirmation that tests pass (`make test`).

## Additional Notes
* Security: Never commit raw contact data; use the `tmp/` folder for temporary test fixtures only.
* Configuration: Runtime settings are read from environment variables; see `project/Specs.md` for details.
* Architecture overview is documented in `project/Architecture.md`.

---
This guide is a living document – update it as the project evolves.
