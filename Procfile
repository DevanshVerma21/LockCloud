# Procfile for Railway/Heroku deployment  
# --preload loads app before forking workers (encodings shared across workers)
web: gunicorn cloud_server:app --workers 2 --threads 4 --timeout 120 --preload
