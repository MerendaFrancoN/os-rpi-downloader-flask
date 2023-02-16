import os

import dotenv
import flask
from celery import Celery
from werkzeug.utils import import_string

from .app import create_flask_app
from .celery_app import celery_app
from .routes import index, progress, enqueue_iso_download, get_available_OS
from .utility.celery_util import init_celery


# celery -A app.runcelery.celery_app worker -c 1 --loglevel=DEBUG


def _configure_celery_app(app: flask.Flask, celery: Celery):
    celery.conf.update(app.config)


def _get_config_from_env():
    app_settings = os.getenv("APP_SETTINGS", "app.env_config.DevelopmentConfig")
    Config = import_string(app_settings)
    return Config()


dotenv.load_dotenv()
CONFIG = _get_config_from_env()
app = create_flask_app(CONFIG)
_configure_celery_app(app, celery_app)
init_celery(app, celery_app)


app.add_url_rule("/", view_func=index)
app.add_url_rule("/enqueueISO", view_func=enqueue_iso_download)
app.add_url_rule("/progress", view_func=progress)
app.add_url_rule("/availableISOs", view_func=get_available_OS)
