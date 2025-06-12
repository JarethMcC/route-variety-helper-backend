# Gunicorn config file

# The address to bind to.
bind = "0.0.0.0:8000"

# The number of worker processes.
# A common recommendation is 2-4 x $(NUM_CORES)
workers = 4

# The type of worker class.
worker_class = "sync"

# The location of the log files.
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# The verbosity of the log output.
loglevel = "info"