# Kiwi weekend thingie
## Installation:
`pip install -r requirements.txt`
## Testing:
Although the test coverage has gotten worse and worse, some tests can still be run with `pytest` or `pytest -sxk ""` for integration testing.
## Flask run:
`FLASK_ENV=development FLASK_APP=backend.py flask run` to run debug flask server. By default it will try to connect to the common redis, but can be forced to run local.
