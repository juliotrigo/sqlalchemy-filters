Release Notes
=============

Here you can see the full list of changes between sqlalchemy-filters
versions, where semantic versioning is used: *major.minor.patch*.


0.12.0
------

Released 2020-05-12

* Add support for hybrid attributes (properties and methods): filtering
  and sorting (#45) as a continuation of the work started here (#32)
  by @vkylamba
  - Addresses (#22)

0.11.0
------

Released 2020-04-25

* Add support for the ``not_ilike`` operator (#40) thanks to @bodik
* Add support for the ``any`` and ``not_any`` operators (#36) thanks
  to @bodik
* Add ability to use the ``select_from`` clause to apply filters
  (#34) thanks to @bodik
* Add new parameter to ``apply_filters`` to disable ``auto_join`` on
  demand (#35) thanks to @bodik
* Add support for Python 3.8 (#43)
* Drop support for Python 3.4 (#33)
* Fix Python 3.7 deprecations (#41) thanks to @bodik
* Add multiple SQLAlchemy versions support: ``1.0``, ``1.1``, ``1.2``,
  ``1.3`` (#33)

0.10.0
------

Released 2019-03-13

* Add ``nullsfirst`` and ``nullslast`` sorting options (#30)

0.9.0
-----

Released 2019-03-07

* Add compatibility (no official support) with Python 2.7 (#23 which
  addresses #18 thanks to @itdependsnetworks)
* Add support for Python 3.7 (#25)
* Add support (tests) for PostgreSQL (#28)
* Fix and improve documentation (#21 thanks to @daviskirk, #28)

0.8.0
-----

Released 2018-06-25

* Adds support for ``ilike`` (case-insensitive) string comparison (#19
  thanks to @rockwelln)
* Drop support for Python 3.3 (#20)

0.7.0
-----

Released 2018-02-12

* Filters and sorts on related models now result in an "automatic join"
  if the query being filtered does not already contain the related model

0.6.0
-----

Released 2017-11-30

* Adds support for restricting the columns that are loaded from the
  database.

0.5.0
-----

Released 2017-11-15

* Adds support for queries against multiple models, e.g. joins.

0.4.0
-----

Released 2017-06-21

* Adds support for queries based on model fields or aggregate functions.

0.3.0
-----

Released 2017-05-22

* Adds support for boolean functions within filters
* Adds the possibility of supplying a single dictionary as filters when
  only one filter is provided
* Makes the ``op`` filter attribute optional: ``==`` is the default
  operator

0.2.0
-----

Released 2017-01-06

* Adds apply query pagination
* Adds apply query sort
* Adds Travis CI
* Starts using Tox
* Refactors Makefile and conftest

0.1.0
-----

Released 2016-09-08

* Initial version
* Adds apply query filters
