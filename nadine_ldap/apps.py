# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig

class NadineLdapConfig(AppConfig):
    name = 'nadine_ldap'

    def ready(self):
        # Load and connect signal recievers
        import nadine_ldap.signals