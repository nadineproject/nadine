# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class NextcloudConfig(AppConfig):
    name = 'nextcloud'

    def ready(self):
        # Load and connect signal receivers
        import nextcloud.signals
