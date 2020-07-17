PYTHON_BIN ?= poetry run python
ENV ?= pypitest

format: isort black

black:
	$(PYTHON_BIN) -m black --target-version py37 --exclude '/(\.git|\.hg|\.mypy_cache|\.nox|\.tox|\.venv|_build|buck-out|build|dist|node_modules|webpack_bundles)/' .

isort:
	$(PYTHON_BIN) -m isort -rc src

publish:
	poetry publish --build
