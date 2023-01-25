import logging
import tempfile
from datetime import datetime
from random import random

import requests
from flask_socketio import SocketIO
from threading import Lock

from flask import Flask, request, send_file, Response

"""
Background Thread
"""
thread = None
thread_lock = Lock()


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")


def background_thread():
    print("Generating random sensor values")
    while True:
        dummy_sensor_value = round(random() * 100, 3)
        socketio.emit('updateSensorData',
                      {'value': dummy_sensor_value, "date": get_current_datetime()})
        socketio.sleep(1)

app = Flask(__name__)
socketio = SocketIO(app, logger=True, cors_allowed_origins="*")


"""
Serve root index file
"""


@app.route('/')
def index():
    return 'Hello World!'


@app.route('/download')
def download_iso():
    url = 'https://releases.ubuntu.com/22.04.1/ubuntu-22.04.1-desktop-amd64.iso'
    try:
        r = requests.get(url, stream=True)
        if r.status_code == 200:
            # create a temporary file and save the downloaded data
            with tempfile.NamedTemporaryFile() as tf:
                for chunk in r.iter_content(1024):
                    tf.write(chunk)
                tf.seek(0)
                return send_file(tf.name, as_attachment=True, attachment_filename='file.iso', mimetype='application/octet-stream')
        else:
            return "Error: Could not download the file"
    except Exception as e:
        return str(e)

"""
Decorator for connect
"""

def download_file_with_progress():
    url = 'http://research.nhm.org/pdfs/4889/4889-001.pdf'
    r = requests.get(url, stream=True)
    total_size = int(r.headers.get('content-length', 0))
    block_size = 1024
    wrote = 0
    with tempfile.NamedTemporaryFile() as tf:
        for data in r.iter_content(block_size):
            wrote = wrote + len(data)
            tf.write(data)
            percentage = (wrote * 100.0) / total_size
            socketio.emit('percentage',
                          {'value': percentage, "date": get_current_datetime()})
        tf.seek(0)
        yield tf

@app.route('/download_progress')
def download_iso_with_progress():

    try:
        return Response(download_file_with_progress(), mimetype='text/event-stream')
    except Exception as e:
        return str(e)









@socketio.on('connect')
def connect():
    global thread
    print('Client connected')

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)


"""
Decorator for disconnect
"""


@socketio.on('disconnect')
def disconnect():
    print('Client disconnected', request.sid)


if __name__ == '__main__':
    socketio.run(app)
