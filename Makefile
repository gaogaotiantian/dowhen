build:
	python -m build

install:
	pip install -e .

lint:
	ruff check src tests
	ruff format src tests --diff
	mypy src

lint-fix:
	ruff check src tests --fix
	ruff format src tests

test:
	pytest --cov=dowhen --cov-report=term-missing:skip-covered tests

.PHONY: docs

docs:
	cd docs && make html

docs-clean:
	cd docs && make clean

clean:
	rm -rf __pycache__
	rm -rf tests/__pycache__
	rm -rf src/dowhen/__pycache__
	rm -rf build
	rm -rf dist
	rm -rf dowhen.egg-info
	rm -rf src/dowhen.egg-info
	rm -rf docs/_build
