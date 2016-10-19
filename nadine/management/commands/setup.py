import os
import string
import random

from django.core.management.base import BaseCommand, CommandError

PROMPT = '> '

class Command(BaseCommand):
    help = "System Setup"
    requires_system_checks = False

    def handle(self, **options):
        print("How long should the secret key be (say 63)?")
        secret_key_len = int(raw_input(PROMPT))
        SECRET_KEY = ''.join([random.SystemRandom().choice("{}{}{}".format(string.ascii_letters, string.digits, string.punctuation)) for i in range(secret_key_len)])
        print("SECRET_KEY = '%s'" % SECRET_KEY)
