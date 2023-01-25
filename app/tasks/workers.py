import tempfile

import requests
from ..celery_app import celery_app
@celery_app.task
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
            celery_app.current_task.update_state(state='PROGRESS',
                                             meta={'current': wrote,
                                                   'total': total_size})
        tf.seek(0)
