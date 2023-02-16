import json
from itertools import chain
from typing import Dict, List

from celery.result import AsyncResult
from flask import render_template_string, request, Response

from .celery_app import celery_app
from .tasks import download_file_with_progress


def index():
    return render_template_string(
        """<a href="{{ url_for('.enqueue') }}">launch job</a>"""
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
                    os_id=job.result["os_id"],
                    state=job.state,
                    progress=job.result["current"] * 1.0 / job.result["total"],
                )
            )
        elif job.state == "SUCCESS":
            return json.dumps(
                dict(
                    os_id=job.result["os_id"],
                    state=job.state,
                    progress=1.0,
                )
            )
    return Response("{}", status=404, mimetype='application/json')


def enqueue_iso_download():
    os_id = request.values.get("id")
    os_entry = _get_available_OS().get(int(os_id))
    job = download_file_with_progress.delay(
        url=os_entry.get("url"),
        os_id=os_id,
    )
    return {"job_id": job.id}


def get_available_OS() -> List[Dict]:
    # 1. Get Available OSes
    available_os = _get_available_OS()

    # 2. Get Running Tasks
    celery_inspector = celery_app.control.inspect()
    active_tasks = list(chain.from_iterable(celery_inspector.active().values()))
    scheduled_tasks = list(chain.from_iterable(celery_inspector.scheduled().values()))
    current_tasks = list(chain.from_iterable([active_tasks, scheduled_tasks]))
    for task in current_tasks:
        job_id = task["id"]
        os_id = task["kwargs"].get("os_id")
        if job_id and os_id:
            available_os[int(os_id)]["job_id"] = job_id

    return list(available_os.values())


def _get_available_OS() -> Dict[int, Dict]:
    with open("app/os_database/db.json") as json_file:
        os_options = json.load(json_file)
        return {os_option["id"]: os_option for os_option in os_options}
