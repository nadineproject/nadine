# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings

import os

OLD_DIR = "member_photo"
NEW_DIR = "user_photos"
 
def forwards_func(apps, schema_editor):
	if not os.path.exists(os.path.join(settings.MEDIA_ROOT, NEW_DIR)): 
		os.makedirs(os.path.join(settings.MEDIA_ROOT, NEW_DIR))

	Member = apps.get_model("staff", "Member")
	for member in Member.objects.all():
		if member.photo:
			filename = member.photo.path.split('/')[-1]
			ext = filename.split('.')[-1].lower()
			new_file = "%s/%s.%s" % (NEW_DIR, member.user.username, ext)
			try:
				print "user: %s, file: %s" % (member.user.username, member.photo.path)
				os.rename(member.photo.path, os.path.join(settings.MEDIA_ROOT, new_file))
				member.photo = new_file
				member.save()
			except:
				print "Can not move %s" % member.photo.path

def reverse_func(apps, schema_editor):
	return

class Migration(migrations.Migration):

	dependencies = [
		('staff', '0005_fileupload_document_type'),
	]

	operations = [
		migrations.RunPython(forwards_func, reverse_func)
	]
