.PHONY: test

POSTGRES_VERSION?=9.6
MYSQL_VERSION?=5.7


rst-lint:
	rst-lint README.rst
	rst-lint CHANGELOG.rst

flake8:
	flake8 sqlalchemy_filters test setup.py

test: flake8
	pytest test $(ARGS)

coverage: flake8 rst-lint
	coverage run --source sqlalchemy_filters -m pytest test $(ARGS)
	coverage report --show-missing --fail-under 100


# Docker test containers

mysql-container:
	docker run -d --rm --name mysql-sqlalchemy-filters -p 3306:3306 \
		-e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
		mysql:$(MYSQL_VERSION)

postgres-container:
	docker run -d --rm --name postgres-sqlalchemy-filters -p 5432:5432 \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_HOST_AUTH_METHOD=trust \
		-e POSTGRES_DB=test_sqlalchemy_filters \
		-e POSTGRES_INITDB_ARGS="--encoding=UTF8 --lc-collate=en_US.utf8 --lc-ctype=en_US.utf8" \
		postgres:$(POSTGRES_VERSION)
