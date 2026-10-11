PYTHON ?= python

.PHONY: setup run doctor report test cov lint type format gif release

## setup: install forgefix + dev tooling and git hooks
setup:
	$(PYTHON) -m pip install -e ".[dev]"
	@command -v pre-commit >/dev/null 2>&1 && pre-commit install || echo "pre-commit not installed; skipping hooks"

## run: show the CLI help
run:
	$(PYTHON) -m forgefix --help

## doctor: run the health check on the current directory
doctor:
	$(PYTHON) -m forgefix doctor

## report: write reports/forgefix-report.md for the current directory
report:
	$(PYTHON) -m forgefix report

## test: run the test suite (coverage gate enforced via pyproject)
test:
	$(PYTHON) -m pytest -q

## cov: run tests with a full coverage report + HTML output
cov:
	$(PYTHON) -m pytest -q --cov-report=term-missing --cov-report=html

## lint: ruff lint + format check (same as CI)
lint:
	ruff check .
	ruff format --check .

## type: mypy over the package (same as CI)
type:
	mypy forgefix

## format: autofix + rewrite files in place
format:
	ruff check --fix .
	ruff format .

## gif: regenerate demo/demo.gif + demo/demo.mp4 with vhs (see CONTRIBUTING.md)
gif:
	vhs demo/demo.tape -o demo/demo.mp4

## release: tag and push a release (usage: make release TAG=v0.2.0)
release:
	@test -n "$(TAG)" || (echo "usage: make release TAG=v0.2.0" && exit 1)
	git tag "$(TAG)"
	git push origin "$(TAG)"
