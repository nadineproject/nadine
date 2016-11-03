# -*- coding: utf-8 -*-
import django.dispatch

email_received = django.dispatch.Signal(providing_args=["instance","attachments"])