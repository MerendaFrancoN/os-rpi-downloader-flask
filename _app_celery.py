'''
testing celery progress reporting/polling
* start server
python tempserver.py
* start worker
celery -A tempserver.celery worker -c 1 --loglevel=DEBUG
* browse to localhost:5000/
'''

import json
import tempfile
import time

import requests
from celery import Celery
from celery.result import AsyncResult
from flask import Flask, request, render_template_string

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/0'
app.config['CELERY_IGNORE_RESULT'] = False
celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'], debug=True)
celery.conf.update(app.config)


@celery.task
def slow_proc():
    n = 10
    for i in range(0, n):
        celery.current_task.update_state(state='PROGRESS',
                                         meta={'current': i, 'total': n})
        time.sleep(2)

    return n


@celery.task
def download_file_with_progress():
    url = 'http://research.nhm.org/pdfs/4889/4889-001.pdf'
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


@app.route('/progress')
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


@app.route('/enqueue')
def enqueue():
    job = download_file_with_progress.delay()
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


@app.route('/')
def index():
    return render_template_string('''\
<a href="{{ url_for('.enqueue') }}">launch job</a>
''')


if __name__ == '__main__':
    app.run(debug=True)
