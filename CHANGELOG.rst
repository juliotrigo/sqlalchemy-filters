Release Notes
=============

Here you can see the full list of changes between sqlalchemy-filters
versions, where semantic versioning is used: *major.minor.patch*.


Version 0.10.0
--------------

Released 2019-03-12

* Add ``nullsfirst`` and ``nullslast`` sorting options (#30)


Version 0.9.0
-------------

Released 2019-03-07

* Add compatibility (no official support) with Python 2.7 (#23 which
  addresses #18 thanks to @itdependsnetworks)
* Add support for Python 3.7 (#25)
* Add support (tests) for PostgreSQL (#28)
* Fix and improve documentation (#21 thanks to @daviskirk, #28)


Version 0.8.0
-------------

Released 2018-06-25

* Adds support for ``ilike`` (case-insensitive) string comparison (#19
  thanks to @rockwelln)
* Drop support for Python 3.3 (#20)


Version 0.7.0
-------------

Released 2018-02-12

* Filters and sorts on related models now result in an "automatic join"
  if the query being filtered does not already contain the related model

Version 0.6.0
-------------

Released 2017-11-30

* Adds support for restricting the columns that are loaded from the
  database.

Version 0.5.0
-------------

Released 2017-11-15

* Adds support for queries against multiple models, e.g. joins.

Version 0.4.0
-------------

Released 2017-06-21

* Adds support for queries based on model fields or aggregate functions.

Version 0.3.0
-------------

Released 2017-05-22

* Adds support for boolean functions within filters
* Adds the possibility of supplying a single dictionary as filters when
  only one filter is provided
* Makes the ``op`` filter attribute optional: ``==`` is the default
  operator

Version 0.2.0
-------------

Released 2017-01-06

* Adds apply query pagination
* Adds apply query sort
* Adds Travis CI
* Starts using Tox
* Refactors Makefile and conftest

Version 0.1.0
-------------

Released 2016-09-08

* Initial version
* Adds apply query filters
