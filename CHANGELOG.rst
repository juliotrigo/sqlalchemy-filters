Release Notes
=============

Here you can see the full list of changes between sqlalchemy-filters
versions, where semantic versioning is used: *major.minor.patch*.

Backwards-compatible changes increment the minor version number only.

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
* Makes the `op` filter attribute optional: `==` is the default operator

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
