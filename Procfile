web: gunicorn --bind :8000 --workers 4 --worker-class sync --timeout 120 --keep-alive 5 --max-requests 1000 --max-requests-jitter 100 --log-level info application:application
