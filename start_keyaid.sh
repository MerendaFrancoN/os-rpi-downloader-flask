export FLASK_APP="/home/pi/Projects/os_downloader_flask/app/runcelery"

/home/pi/.local/bin/poetry install
/home/pi/.local/bin/poetry -C /home/pi/Projects/os_downloader_flask run flask run --host 0.0.0.0 --port 5000
