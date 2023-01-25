'''
testing celery progress reporting/polling
* start server
python tempserver.py
* start worker
celery -A tempserver.celery worker -c 1 --loglevel=DEBUG
* browse to localhost:5000/
'''
# https://stackoverflow.com/questions/16221295/python-flask-with-celery-out-of-application-context
import os
import json
import tempfile

import requests
from celery.result import AsyncResult
from flask import request, render_template_string

import dotenv
import flask
from celery import Celery
from werkzeug.utils import import_string

from app.routes import index

dotenv.load_dotenv()



def _configure_flask_app(app: flask.Flask, config: flask.Config = None):
    app.config.from_object(config)


def _configure_celery_app(app: flask.Flask, celery: Celery):
    celery.conf.update(app.config)


def _get_config_from_env():
    app_settings = os.getenv("APP_SETTINGS", "app.env_config.DevelopmentConfig")
    Config = import_string(app_settings)
    return Config()

def create_flask_app():
    app = flask.Flask(__name__)
    celery = Celery(app.name, broker=os.getenv('CELERY_BROKER_URL'), debug=True)

    config = _get_config_from_env()
    _configure_flask_app(app, config)
    _configure_celery_app(app, celery)
    return app, celery

app, celery = create_flask_app()

@celery.task
def download_file_with_progress(url: str):
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0
    with tempfile.NamedTemporaryFile(dir="/Users/stormtrooper/Downloads/",
                                     suffix=".pdf") as tf:
        for data in r.iter_content(block_size):
            wrote = wrote + len(data)
            tf.write(data)
            celery.current_task.update_state(state='PROGRESS',
                                             meta={'current': wrote,
                                                   'total': total_size})
        tf.seek(0)

def progress():
    jobid = request.values.get('jobid')
    if jobid:
        # GOTCHA: if you don't pass app=celery here,
        # you get "NotImplementedError: No result backend configured"
        job = AsyncResult(jobid, app=celery)
        if job.state == 'PROGRESS':
            return json.dumps(dict(
                state=job.state,
                progress=job.result['current'] * 1.0 / job.result['total'],
            ))
        elif job.state == 'SUCCESS':
            return json.dumps(dict(
                state=job.state,
                progress=1.0,
            ))
    return '{}'
def enqueue():
    job = download_file_with_progress.delay(
        url='http://research.nhm.org/pdfs/4889/4889-001.pdf'
    )
    return render_template_string('''\
<style>
#prog {
width: 400px;
border: 1px solid #eee;
height: 20px;
}
#bar {
width: 0px;
background-color: #ccc;
height: 20px;
}
</style>
<h3></h3>
<div id="prog"><div id="bar"></div></div>
<div id="pct"></div>
<script src="//code.jquery.com/jquery-2.1.1.min.js"></script>
<script>
function poll() {
    $.ajax("{{url_for('.progress', jobid=JOBID)}}", {
        dataType: "json",
        cache: false,
        success: function(resp) {
            console.log(resp);
            $("#pct").html(resp.progress);
            $("#bar").css({width: $("#prog").width() * resp.progress});
            if(resp.progress >= 0.9) {
                $("#bar").css({backgroundColor: "limegreen"});
                return;
            } else {
                setTimeout(poll, 1000.0);
            }
        }
    });
}
$(function() {
    var JOBID = "{{ JOBID }}";
    $("h3").html("JOB: " + JOBID);
    poll();
});
</script>
''', JOBID=job.id)



app.add_url_rule('/', view_func=index)
app.add_url_rule('/enqueue', view_func=enqueue)
app.add_url_rule('/progress', view_func=progress)
