# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

class LDAPSyncConfig(AppConfig):
    name = 'ldap_sync'

    def ready(self):
        # Load and connect signal recievers
        import ldap_sync.signals