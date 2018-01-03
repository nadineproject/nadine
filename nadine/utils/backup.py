import os
import time
import urllib.request, urllib.parse, urllib.error
import sys
import datetime
import logging
import tempfile
import shutil
import csv

logger = logging.getLogger(__name__)

from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from nadine.models.profile import EmergencyContact

class BackupError(Exception):
    pass


class BackupManager(object):

    def __init__(self):
        pass

    def call_system(self, command):
        if os.system(command) == 0:
            return True
        print(('FAILED:', command))
        return False

    def get_db_info(self):
        if not hasattr(settings, 'DATABASES'):
            raise BackupError('settings.DATABASES is not defined')
        if not 'default' in settings.DATABASES:
            raise BackupError('settings.DATABASES has no default db')
        if settings.DATABASES['default']['ENGINE'] != 'django.db.backends.postgresql':
            raise BackupError('This command only works with PostgreSQL')
        if 'PASSWORD' in settings.DATABASES['default']:
            password = settings.DATABASES['default']['PASSWORD']
        else:
            password = None
        return (settings.DATABASES['default']['USER'], settings.DATABASES['default']['NAME'], password)

    def restore_backup(self, file_path):
        backup_path = os.path.realpath(file_path)
        if not os.path.exists(backup_path):
            raise BackupError('The backup file "%s" does not exist.' % backup_path)
        if not os.path.isfile(backup_path):
            raise BackupError('The specified backup file "%s" is not a file.' % backup_path)
        if not backup_path.endswith('.tar'):
            raise BackupError('The specified backup file "%s" must be a tar file.' % backup_path)

        self.check_dirs()
        db_user, db_name, db_password = self.get_db_info()

        logger.debug('Restoring from backup file "%s"' % backup_path)

        # create the working directory
        working_dir = tempfile.mkdtemp('backup-temp')

        # untar the backup file, which should result in two files: sql and media
        command = 'cd "%s" && tar -xzf "%s"' % (working_dir, backup_path)
        if not self.call_system(command):
            raise BackupError('Aborting restoration.')

        # create a sub directory for the media, and untar it
        command = 'cd "%s" && tar -xzf %s/*-media.tgz' % (working_dir, working_dir)
        if not self.call_system(command):
            raise BackupError('Aborting restoration.')

        # move each media dir from the temp media dir into the project media dir
        media_dir = os.path.join(working_dir, 'media')
        if not os.path.exists(media_dir):
            raise BackupError('Could not restore the media dir')
        for media_file in os.listdir(media_dir):
            target = os.path.join(settings.MEDIA_ROOT, media_file)
            if os.path.exists(target) and os.path.isdir(target):
                shutil.rmtree(target)
            if os.path.exists(target):
                os.remove(target)
            shutil.move(os.path.join(media_dir, media_file), target)

        if db_password:
            os.environ['PGPASSWORD'] = db_password

        # now delete and recreate the database
        if db_user:
            command = 'echo "drop database %s; create database %s; grant all on database %s to %s;" | psql -U %s postgres' % (db_name, db_name, db_name, db_user, db_user)
        else:
            command = 'echo "drop database %s; create database %s;" | psql postgres' % (db_name, db_name)
        if not self.call_system(command):
            raise BackupError('Aborting restoration.')

        # now load the SQL into the database
        if db_user:
            command = 'gunzip -c %s/*-sql.gz | psql -U %s %s' % (working_dir, db_user, db_name)
        else:
            command = 'gunzip -c %s/*-sql.gz | psql %s' % (working_dir, db_name)
        if not self.call_system(command):
            raise BackupError('Aborting restoration.')

    def check_dirs(self):
        if not hasattr(settings, 'MEDIA_ROOT'):
            raise BackupError('The MEDIA_ROOT is not defined')
        if not os.path.exists(settings.MEDIA_ROOT):
            raise BackupError('MEDIA_ROOT "%s" does not exist.' % settings.MEDIA_ROOT)
        if not os.path.isdir(settings.MEDIA_ROOT):
            raise BackupError('MEDIA_ROOT "%s" is not a directory.' % settings.MEDIA_ROOT)

        if not hasattr(settings, 'BACKUP_ROOT'):
            raise BackupError('You must define BACKUP_ROOT in settings.py')
        if not os.path.exists(settings.BACKUP_ROOT):
            os.makedirs(settings.BACKUP_ROOT)
        if not os.path.exists(settings.BACKUP_ROOT):
            raise BackupError('Backup root "%s" does not exist' % settings.BACKUP_ROOT)
        if not os.path.isdir(settings.BACKUP_ROOT):
            raise BackupError('Backup root "%s" is not a directory' % settings.BACKUP_ROOT)

    def remove_old_files(self):
        file_count = 0
        files = os.listdir(settings.BACKUP_ROOT)
        files.sort()
        files.reverse()
        for f in files:
            if f == "latest-backup.tar":
                continue
            if f.endswith("-backup.tar"):
                if file_count < settings.BACKUP_COUNT:
                    file_count = file_count + 1
                else:
                    logger.warn("Removing old log file: %s" % f)
                    os.remove(settings.BACKUP_ROOT + f)

    def make_backup(self):
        self.check_dirs()
        db_user, db_name, db_password = self.get_db_info()

        now = timezone.localtime(timezone.now())
        file_token = '%d-%02d-%02d_%02d-%02d-%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)

        sql_file = '%s-sql.gz' % file_token
        sql_path = '%s%s' % (settings.BACKUP_ROOT, sql_file)
        sql_pass_args = ''
        if db_password:
            os.environ['PGPASSWORD'] = db_password
        command = 'pg_dump -U %s %s | gzip > "%s"' % (db_user, db_name, sql_path)
        if not self.call_system(command):
            print('aborting')
            return

        media_file = '%s-media.tgz' % file_token
        media_path = '%s%s' % (settings.BACKUP_ROOT, media_file)
        dirs = settings.MEDIA_ROOT.split('/')
        command = 'cd "%s" && cd .. && tar -czf "%s" "%s"' % (settings.MEDIA_ROOT, media_path, dirs[len(dirs) - 1])
        if not self.call_system(command):
            print('aborting')
            return

        backup_file = '%s-backup.tar' % file_token
        backup_path = '%s%s' % (settings.BACKUP_ROOT, backup_file)
        print(("backup_file: %s" % backup_file))
        command = 'cd "%s" && tar -czf "%s" "%s" "%s"' % (settings.BACKUP_ROOT, backup_path, media_file, sql_file)
        if not self.call_system(command):
            print('aborting')
            return

        if not self.call_system('cd "%s" && ln -fs "%s" latest-backup.tar' % (settings.BACKUP_ROOT, backup_file)):
            print(('Could not link %s to latest-backup.tar' % backup_file))

        command = 'rm -f "%s" "%s"' % (media_path, sql_path)
        if not self.call_system(command):
            print('Could not erase temp backup files')

        if settings.BACKUP_COUNT and settings.BACKUP_COUNT > 0:
            self.remove_old_files()

        return os.path.join(settings.BACKUP_ROOT, backup_path)

    def export_active_users(self):
        filename = settings.BACKUP_ROOT + 'active_members.csv'

        csv_data = [[
            'username',
            'first_name',
            'last_name',
            'email',
            'phone',
            'phone2',
            'address1',
            'address2',
            'city',
            'state',
            'zipcode',
            'has_key',
            'emergency_contact',
            'ec_relationship',
            'ec_phone',
            'ec_email',
        ]]
        for user in User.helper.active_members():
            ec = EmergencyContact.objects.filter(user=user).first()
            row = [
                user.username,
                user.first_name,
                user.last_name,
                user.email,
                user.profile.phone,
                user.profile.phone2,
                user.profile.address1,
                user.profile.address2,
                user.profile.city,
                user.profile.state,
                user.profile.zipcode,
            ]

            if user.membership.has_key():
                row.append('True')
            else:
                row.append('')

            if ec and ec.name:
                row.append(ec.name)
                row.append(ec.relationship)
                row.append(ec.phone)
                row.append(ec.email)
            else:
                row.append('None')
                row.append('')
                row.append('')
                row.append('')

            csv_data.append(row)

        # Write out our CSV
        with open(filename, 'w') as f:
            writer = csv.writer(f)
            writer.writerows(csv_data)
