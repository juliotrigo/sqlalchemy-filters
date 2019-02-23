.PHONY: test

POSTGRES_VERSION?=9.6.9
MYSQL_VERSION?=5.7


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


# Docker test containers

docker-mysql-run:
	docker run -d --name mysql-postgres-sqlalchemy-filters -p 3306:3306 \
		-e MYSQL_ALLOW_EMPTY_PASSWORD=yes \
		mysql:$(MYSQL_VERSION)

docker-postgres-run:
	docker run -d --name postgres-sqlalchemy-filters -p 5432:5432 \
		-e POSTGRES_USER=postgres \
		-e POSTGRES_PASSWORD= \
		-e POSTGRES_DB=test_sqlalchemy_filters \
		-e POSTGRES_INITDB_ARGS="--encoding=UTF8 --lc-collate=en_US.utf8 --lc-ctype=en_US.utf8" \
		postgres:$(POSTGRES_VERSION)
