PYTHON_BIN ?= poetry run python

format:
	$(PYTHON_BIN) -m monoformat --py-src-path src/model_w/project_maker/template/api/src .
