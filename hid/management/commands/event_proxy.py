import os
import time
import urllib
import sys
import requests

from datetime import datetime

import django
from django.core.handlers import base, wsgi
from django import http
from django.conf import settings
from django.utils import timezone
from django.core.management.base import BaseCommand, CommandError
from django.core.servers.basehttp import WSGIRequestHandler, run, get_internal_wsgi_application
from django.core.handlers.base import BaseHandler

class SimpleRequest(wsgi.WSGIRequest):
    def __init__(self, environ):
        self.environ = environ
        self.path_info = wsgi.get_path_info(environ)
        self.script_name = wsgi.get_script_name(environ)
        self.path = "unknown"
        self.META = environ
        self.META['PATH_INFO'] = self.path_info
        self.META['SCRIPT_NAME'] = self.script_name
        self.method = environ['REQUEST_METHOD'].upper()
        self.status = ""

class SimpleHandler(wsgi.WSGIHandler):
    def __call__(self, environ, start_response):
        status = "200 OK"
        #request = self.request_class(environ)
        #request = SimpleRequest(environ)
        request = wsgi.WSGIRequest(environ)
        print request
        start_response(status, [])
        #self.load_middleware()
        #response = self.get_response(request)
        #return response
        #super(wsgi.WSGIHandler).__call__(self, environ, start_response)

class Command(BaseCommand):
    help = "Start up a simple HTTP server to proxy events"
    args = ""
    requires_system_checks = False

    def handle(self, *labels, **options):
        #handler = get_internal_wsgi_application()
        #django.setup(set_prefix=False)
        handler = SimpleHandler()
        #handler = base.BaseHandler()
        run("127.0.0.1", 8000, handler, ipv6=False, threading=False)
