.PHONY: clean

PIP := pip install -r

PROJECT_NAME := libesocial
PYTHON_VERSION := 3.7.2
VENV_NAME := $(PROJECT_NAME)-$(PYTHON_VERSION)

# Environment setup
setup:
	python setup.py install

.clean-build: ## remove build artifacts
	rm -fr build/
	rm -fr dist/
	rm -fr .eggs/
	find . -name '*.egg-info' -exec rm -fr {} +
	find . -name '*.egg' -exec rm -f {} +

.clean-pyc: ## remove Python file artifacts
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

.clean-test: ## remove test and coverage artifacts
	rm -fr .tox/
	rm -f .coverage
	rm -fr htmlcov/
	rm -fr reports/
	rm -fr .pytest_cache/

clean: .clean-build .clean-pyc .clean-test ## remove all build, test, coverage and Python artifacts

.create-venv:
	pyenv install -s $(PYTHON_VERSION)
	pyenv uninstall -f $(VENV_NAME)
	pyenv virtualenv $(PYTHON_VERSION) $(VENV_NAME)
	pyenv local $(VENV_NAME)

create-venv: .create-venv setup

# Build
release:
	python setup.py sdist bdist_wheel

dist-test:
	twine upload --repository-url https://test.pypi.org/legacy/ dist/*

distribution:
	twine upload dist/*
