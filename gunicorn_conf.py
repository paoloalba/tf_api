# from pprint import pprint

# this is the default log format
# access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
# access_log_format = '%%({X-Forwarded-For}i)s'
# access_log_format = '%({X-SSL-CERT}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
access_log_format = '%({X-Forwarded-For}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

workers = 1
worker_class = 'sync'
# worker_class = 'gthread'
# if thread >1 gthread is used automatically
# threads = 1

##### time to on a silent worker (starting or serving a request) before restarting
timeout = 120

errorlog = "-"
accesslog = "-"
