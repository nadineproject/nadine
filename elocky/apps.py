# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class ElockyConfig(AppConfig):
    name = 'elocky'

    def ready(self):
        # Load and connect signal receivers
        import elocky.signals
