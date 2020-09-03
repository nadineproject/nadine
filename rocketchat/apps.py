# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig


class RocketchatConfig(AppConfig):
    name = 'rocketchat'

    def ready(self):
        # Load and connect signal receivers
        import rocketchat.signals
