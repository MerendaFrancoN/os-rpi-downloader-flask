import json
import os
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
    response = Response(json.dumps({}), mimetype="application/json")
    if jobid:
        # GOTCHA: if you don't pass app=celery here,
        # you get "NotImplementedError: No result backend configured"
        job = AsyncResult(jobid, app=celery_app)
        if job.state == "PROGRESS":
            response = Response(
                json.dumps(
                    dict(
                        os_id=job.result["os_id"],
                        state=job.state,
                        progress=job.result["current"] * 1.0 / job.result["total"],
                    )
                )
            )
        elif job.state == "SUCCESS":
            response = Response(
                json.dumps(
                    dict(
                        state=job.state,
                        progress=1.0,
                    )
                )
            )
        return response

    return response


def enqueue_iso_download():
    os_id = request.values.get("id")
    os_entry = _get_available_OS().get(int(os_id))
    job = download_file_with_progress.delay(
        url=os_entry.get("url"),
        os_id=os_id,
        filename=os_entry.get("filename")
    )
    response = Response(json.dumps({"job_id": job.id}))
    return response


def remove_os():
    os_id = request.values.get("id")
    os_entry = _get_available_OS().get(int(os_id))
    os.remove(f"/mass_storage/temp_storage/{os_entry.get('filename')}")
    response = Response(status=200)
    return response



def get_available_OS() -> Response:
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
        is_installing = job_id and os_id
        if is_installing:
            available_os[int(os_id)]["job_id"] = job_id
    response = Response(
        json.dumps(list(available_os.values())),
        mimetype="application/json"
    )
    return response


def _get_available_OS() -> Dict[int, Dict]:
    root = os.path.abspath("")
    with open(f"{root}/app/os_database/db.json") as json_file:
        os_options = json.load(json_file)
        available_os = {os_option["id"]: os_option for os_option in os_options}
        for os_id, os_value in available_os.items():
            available_os[os_id]["is_installed"] = _is_OS_installed(available_os[os_id]["filename"])
        return available_os



def _is_OS_installed(os_filename: str) -> bool:
    path = "/mass_storage/temp_storage"
    file_list = os.listdir(path)
    os_files = [file_name for file_name in file_list if os_filename == file_name]
    return bool(os_files)