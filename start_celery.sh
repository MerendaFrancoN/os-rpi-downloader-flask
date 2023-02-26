/home/pi/.local/bin/poetry install
/home/pi/.local/bin/poetry -C /home/pi/Projects/os_downloader_flask/ run celery --workdir "/home/pi/Projects/os_downloader_flask" -A app.runcelery.celery_app worker -c 1 --loglevel=DEBUG
