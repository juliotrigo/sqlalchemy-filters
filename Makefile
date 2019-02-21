.PHONY: test


rst-lint:
	rst-lint README.rst
	rst-lint CHANGELOG.rst

flake8:
	flake8 sqlalchemy_filters test

test: flake8
	pytest test $(ARGS)

coverage: flake8 rst-lint
	coverage run --source sqlalchemy_filters -m pytest test $(ARGS)
	coverage report -m --fail-under 100
