VENV=$(PWD)/env

.PHONY: all lint mypy tests
all:  lint mypy tests


$(VENV):
	python -m venv $@
	$(VENV)/bin/pip install -e '.[dev]'


lint: $(VENV)
	$(VENV)/bin/ruff format --diff
	$(VENV)/bin/ruff check


mypy: $(VENV)
	$(VENV)/bin/mypy .


tests: $(VENV)
	$(VENV)/bin/pytest -vv
