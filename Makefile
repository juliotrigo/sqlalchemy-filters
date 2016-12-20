.PHONY: test


flake8:
	flake8 sqlalchemy_filters test

test: flake8
	@py.test test $(ARGS)

coverage: flake8
	coverage run --source sqlalchemy_filters -m pytest test $(ARGS)
	coverage report -m --fail-under 100
