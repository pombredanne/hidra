# -*- coding: utf-8 -*-

from flask import request
from werkzeug import LocalProxy


def log_request(self):
    log = self.server.log
    if log:
        if hasattr(log, 'info'):
            log.info(self.format_request() + '\n')
        else:
            log.write(self.format_request() + '\n')


# Monkeys are made for freedom.
try:
    import gevent
    from geventwebsocket.gunicorn.workers import GeventWebSocketWorker as Worker
except ImportError:
    pass

if 'gevent' in locals():
    # Freedom-Patch logger for Gunicorn.
    if hasattr(gevent, 'pywsgi'):
        gevent.pywsgi.WSGIHandler.log_request = log_request


websocket = LocalProxy(lambda: request.environ.get('wsgi.websocket', None))

# CLI sugar.
if 'Worker' in locals():
    worker = Worker
