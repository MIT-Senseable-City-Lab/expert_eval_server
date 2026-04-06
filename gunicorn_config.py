# Gunicorn configuration for bumblebee evaluation app

bind = "127.0.0.1:5050"
workers = 2  # Local Mac doesn't need many workers
worker_class = "sync"
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "bumblebee_eval"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Preload app for better performance
preload_app = True

# Graceful timeout
graceful_timeout = 30
