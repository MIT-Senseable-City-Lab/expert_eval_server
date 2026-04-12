# Gunicorn configuration for calibration mode (port 5051)

bind = "127.0.0.1:5051"
workers = 1
worker_class = "sync"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "logs/access_calibration.log"
errorlog = "logs/error_calibration.log"
loglevel = "info"

# Process naming
proc_name = "bumblebee_eval_calibration"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload app for better performance
preload_app = True

# Graceful timeout
graceful_timeout = 30
