import json
from typing import Dict, List

from celery.result import AsyncResult
from flask import render_template_string, request

from .celery_app import celery_app
from .tasks import download_file_with_progress


def index():
    return render_template_string(
        """\
<a href="{{ url_for('.enqueue') }}">launch job</a>
"""
    )


def progress():
    jobid = request.values.get("jobid")
    if jobid:
        # GOTCHA: if you don't pass app=celery here,
        # you get "NotImplementedError: No result backend configured"
        job = AsyncResult(jobid, app=celery_app)
        if job.state == "PROGRESS":
            return json.dumps(
                dict(
                    state=job.state,
                    progress=job.result["current"] * 1.0 / job.result["total"],
                )
            )
        elif job.state == "SUCCESS":
            return json.dumps(
                dict(
                    state=job.state,
                    progress=1.0,
                )
            )
    return "{}"


def enqueue():
    job = download_file_with_progress.delay(
        url="http://research.nhm.org/pdfs/4889/4889-001.pdf"
    )
    return render_template_string(
        """\
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
""",
        JOBID=job.id,
    )


def enqueue_iso_download():
    os_id = request.values.get("id")
    os_entry = _get_available_OS().get(int(os_id))
    job = download_file_with_progress.delay(
        url=os_entry.get("url"),
    )
    return {"job_id": job.id}


def get_available_OS() -> List[Dict]:
    # 1. get running tasks
    # 2. continue checking status
    # 3.
    return list(_get_available_OS().values())


def _get_available_OS() -> Dict[int, Dict]:
    with open("app/os_database/db.json") as json_file:
        os_options = json.load(json_file)
        return {os_option["id"]: os_option for os_option in os_options}
