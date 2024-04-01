# OS Downloader - Flask
Flask Server that was developed to be run by a Raspberry Pi to download different types of OS and mount it in a given OTG Device. The idea is that once the Raspberry Pi is connected to another computer, you can use it as a mass storage and be able to install different types of OS systems.

## Steps to run the application:

1. Run **Flask** App
- ```flask run```
2. Run **Celery** Worker
- ```celery -A app.runcelery.celery_app worker -c 1 --loglevel=DEBUG```
