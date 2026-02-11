# Gunicorn configuration for human identity evaluation app
# This file configures Gunicorn to serve the Flask app

bind = "127.0.0.1:5001"
workers = 4  # Reduced for stability
worker_class = "sync"
worker_connections = 1000
timeout = 60  # Increased timeout for image processing
keepalive = 2
max_requests = 1000
max_requests_jitter = 100

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "human_identity_eval"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Application
module = "wsgi:app"

# Preload app for better performance
preload_app = True

# Graceful timeout
graceful_timeout = 30
