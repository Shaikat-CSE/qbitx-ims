import multiprocessing

bind = "127.0.0.1:8002"
workers = multiprocessing.cpu_count() * 2 + 1
timeout = 120
accesslog = "/var/log/gunicorn/imstransform_access.log"
errorlog = "/var/log/gunicorn/imstransform_error.log"
capture_output = True
loglevel = "info" 