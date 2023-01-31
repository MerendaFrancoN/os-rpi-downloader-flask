"""
testing celery progress reporting/polling
* start server
python tempserver.py
* start worker
celery -A tempserver.celery worker -c 1 --loglevel=DEBUG
* browse to localhost:5000/
"""
# https://stackoverflow.com/questions/16221295/python-flask-with-celery-out-of-application-context

import dotenv
import flask


def _configure_flask_app(app: flask.Flask, config: flask.Config = None):
    app.config.from_object(config)


def create_flask_app(config_obj):
    app = flask.Flask("app")
    _configure_flask_app(app, config_obj)
    return app
