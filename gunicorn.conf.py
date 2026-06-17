# gunicorn.conf.py

bind = "0.0.0.0:8000"

worker_class = "gthread"

workers = 2
threads = 2

timeout = 120
keepalive = 5

accesslog = "-"
errorlog = "-"

capture_output = True