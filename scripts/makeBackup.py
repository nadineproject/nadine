#!/usr/bin/python
import os
import datetime
import sys
import settings
from common_script import *

"""Creates a backup file of the form YYYY-MM-DD_HH-MM-SS-backup.tar in the directory specified by settings.BACKUP_ROOT.
	The file contains the media directories specified by settings.DYNAMIC_MEDIA_DIRS and a mysqldump of the database.
"""

def main():
	now = datetime.datetime.now()
	file_token = '%d-%02d-%02d_%02d-%02d-%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)

	sql_file = '%s-sql.gz' % file_token
	sql_path = '%s%s' % (settings.BACKUP_ROOT, sql_file)
	command = 'mysqldump -u %s %s | gzip > "%s"' % (settings.DATABASE_USER, settings.DATABASE_NAME, sql_path)
	if not call_system(command):
		print 'aborting'
		return

	media_file = '%s-media.tgz' % file_token
	media_path = '%s%s' % (settings.BACKUP_ROOT, media_file)
	command = 'cd "%s" && tar -czf "%s" %s' % (settings.MEDIA_ROOT, media_path, ' '.join(['"%s"' % media_dir for media_dir in settings.DYNAMIC_MEDIA_DIRS]))
	if not call_system(command):
		print 'aborting'
		return
	
	backup_file = '%s%s-backup.tar' % (settings.BACKUP_ROOT, file_token)
	command = 'cd "%s" && tar -czf "%s" "%s" "%s"' % (settings.BACKUP_ROOT, backup_file, media_file, sql_file)
	if not call_system(command):
		print 'aborting'
		return
	
	command = 'rm -f "%s" "%s"' % (media_path, sql_path)
	if not call_system(command): print 'Could not erase temp backup files'
	
	
	
if __name__ == '__main__':
	main()