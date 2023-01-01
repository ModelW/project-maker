PYTHON_BIN ?= poetry run python

format:
	$(PYTHON_BIN) -m monoformat --py-src-path src/model_w/project_maker/template/api/src .

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
