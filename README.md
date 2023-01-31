# OS Downloader - Flask
Steps to run the application:

1. Run **Flask** App
- ```flask run```
2. Run **Celery** Worker
- ```celery -A app.runcelery.celery_app worker -c 1 --loglevel=DEBUG```
