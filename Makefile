PYTHON_BIN ?= poetry run python

TEMPLATE_DIR = src/model_w/project_maker/template

format:
	$(PYTHON_BIN) -m ruff check --fix .
	$(PYTHON_BIN) -m ruff format .
	$(PYTHON_BIN) -m ruff format $(TEMPLATE_DIR)/api
	cd $(TEMPLATE_DIR)/front && pnpm prettier --write .

lint:
	$(PYTHON_BIN) -m ruff check .
	$(PYTHON_BIN) -m ruff format --check .
	$(PYTHON_BIN) -m ruff format --check $(TEMPLATE_DIR)/api
	cd $(TEMPLATE_DIR)/front && pnpm prettier --check .

test:
	$(PYTHON_BIN) -m pytest

test_slow:
	$(PYTHON_BIN) -m pytest -m slow

check_release:
ifndef VERSION
	$(error VERSION is undefined)
endif

release: check_release
	git flow release start $(VERSION)
	sed -i 's/^version =.*/version = "$(VERSION)"/' pyproject.toml
	git add pyproject.toml
	git commit -m "Bump version to $(VERSION)"
	git flow release finish -m "Release $(VERSION)" $(VERSION) > /dev/null
