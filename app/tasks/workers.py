import subprocess
import tempfile
from pathlib import Path

import requests

from ..celery_app import celery_app


@celery_app.task
def download_file_with_progress(url: str, os_id: str):
    r = requests.get(
        url,
        stream=True,
        headers={"Access-Control-Allow-Origin": "*"},
    )
    total_size = int(r.headers.get("content-length", 0))
    block_size = 1024
    wrote = 0
    with tempfile.NamedTemporaryFile(
            dir="/Users/stormtrooper/Downloads/", suffix=".pdf"
    ) as tf:
        for data in r.iter_content(block_size):
            wrote = wrote + len(data)
            tf.write(data)
            celery_app.current_task.update_state(
                state="PROGRESS",
                meta={
                    "os_id": os_id,
                    "current": wrote,
                    "total": total_size,
                },
            )
        tf.seek(0)
        # shutil.copy2(tf, "/media/mass_storage")
        # copy_to_mass_storage(tf.gettempdir())


def copy_to_mass_storage(path: Path):
    # 1. Set up loop device
    loop_device = subprocess.run(
        ["sudo", "losetup", "--show", "-f", "-P", "data.bin"], capture_output=True
    ).stdout

    # 2. Mount loop device
    subprocess.run(["sudo", "mount", f"{loop_device}p1", "/mass_storage/temp_storage/"])

    # 3. Copy file
    subprocess.run(["sudo", "cp", path.as_posix()])

    # 4. Umount
    subprocess.run(["sudo", "umount", "/mass_storage/temp_storage/"])
