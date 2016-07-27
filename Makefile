DB_USER ?= root
DB_PASS ?=
DB_SERVER ?= localhost
DB_PORT ?= 3306
DB_NAME ?= test_sqlalchemy_filters
SQLITE_DB_FILE ?= /$(DB_NAME).db
DB_DIALECT ?= sqlite
DB_DRIVER ?= pysqlite

ifeq ($(DB_DIALECT), sqlite)
	DB_URI = $(SQLITE_DB_FILE)
else
	DB_URI = $(DB_USER):$(DB_PASS)@$(DB_SERVER):$(DB_PORT)/$(DB_NAME)
endif

.PHONY: test

test:
	@py.test test -x -vv \
		--test_db_uri $(DB_URI) \
		--test_db_dialect $(DB_DIALECT) \
		--test_db_driver $(DB_DRIVER)

coverage:
	flake8 sqlalchemy_filters test
	coverage run --source sqlalchemy_filters -m pytest test -x -vv \
		--test_db_uri $(DB_URI) \
		--test_db_dialect $(DB_DIALECT) \
		--test_db_driver $(DB_DRIVER)
	coverage report -m --fail-under 100
