import os
import time
import csv
import ConfigParser

from django.template.defaultfilters import slugify
from django.core.management.base import BaseCommand, CommandError
from django.core.files import File

from nadine.models import *
from taggit.models import *

class Command(BaseCommand):
    help = "Clean all the tags"
    def handle(self, **options):
        print("Cleaning all the tags...")
        for tag in Tag.objects.all():
            clean = tag.name.strip().lower()
            if tag.name != clean:
                print ("Found '%s'" % tag.name)
                for user in User.objects.filter(profile__tags__name__in=[tag.name]):
                    print ("   Updating '%s'" % user.username)
                    user.profile.tags.add(clean)
                print ("Deleting '%s'" % tag.name)
                tag.delete()
