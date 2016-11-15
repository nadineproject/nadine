import os
import string
import random
import getpass
import socket

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from pytz import country_names, country_timezones, common_timezones

EXAMPLE_FILE = "nadine/local_settings.example"
SETTINGS_FILE = "nadine/local_settings.py"
PROMPT = '> '

class Command(BaseCommand):
    help = "System Setup"
    requires_system_checks = False

    def handle(self, **options):
        try:
            print
            print("###################################")
            print("Nadine Local Settings Configuration")
            print("###################################")
            print
            self.load_settings_file()
            self.setup_general()
            self.setup_timezone()
            self.setup_database()
            self.write_settings_file()
        except KeyboardInterrupt:
            print
            print("Exiting without saving!")
            print

    def load_settings_file(self):
        # Test to see if SETTINGS_FILE exists and prompt to load it or remove it
        filename = SETTINGS_FILE
        if os.path.isfile(SETTINGS_FILE):
            print ("File '%s' exists!" % SETTINGS_FILE)
            print ("Do you want to load the existing file? (Y, n)")
            load = raw_input(PROMPT).strip().lower()
            if load == "n":
                print("Current settings in '%s' will be lost!" % SETTINGS_FILE)
                filename = EXAMPLE_FILE
        self.local_settings = LocalSettings(filename)
        print

    def write_settings_file(self):
        print("Write new local_settings file? (y, N)")
        save = raw_input(PROMPT).strip().lower()
        if save == "y":
            print("Writing %s" % SETTINGS_FILE)
            self.local_settings.save(SETTINGS_FILE)

    def setup_general(self):
        print("### General Settings ###")

        # Secret Key
        secret_key = self.local_settings.get("SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            print("Generating random SECRET_KEY")
            secret_key = ''.join([random.SystemRandom().choice("{}{}".format(string.ascii_letters, string.digits)) for i in range(63)])
            self.local_settings.set('SECRET_KEY', secret_key, quiet=True)
            print

        # Site Name
        current_host = socket.gethostname().lower()
        print("Site name? (default: 'Nadine')")
        site_name = raw_input(PROMPT).strip()
        if not site_name:
            site_name = "Nadine"
        self.local_settings.set('SITE_NAME', site_name)

        # Site Domain
        print("Site domain? (default: '%s')" % current_host)
        domain = raw_input(PROMPT).strip()
        if not domain:
            domain = current_host
        self.local_settings.set('SITE_DOMAIN', domain)

        # Protocol (http or https)
        protocol = "http"
        print("Use SSL? (y, N)")
        ssl = raw_input(PROMPT).strip().lower()
        if ssl == "y":
            protocol = protocol + "s"
        self.local_settings.set('SITE_PROTO', protocol)

        # System Email Address
        default_email = "nadine@" + domain
        print("System email address? (default: '%s')" % default_email)
        email = raw_input(PROMPT).strip().lower()
        if not email:
            email = default_email
        self.local_settings.set('EMAIL_ADDRESS', email)

    def setup_timezone(self):
        print("### Timezone Setup ###")

        # Country
        country = ''
        while country not in country_names:
            print("What country? (blank: list available)")
            country = raw_input(PROMPT).strip().upper()
            if not country:
                print ("Country Codes:")
                print(', '.join(country_names))
                print
        self.local_settings.set('COUNTRY', country)

        # Timezone
        tz = ''
        while tz not in common_timezones:
            print("What timezone? (blank: list available)")
            tz = raw_input(PROMPT).strip()
            if not tz:
                print ("Available Timezones:")
                print(', '.join(country_timezones[country]))
                print
        self.local_settings.set('TIME_ZONE', tz)

    # Database Setup
    def setup_database(self):
        current_user = getpass.getuser()
        print
        print("### Database Setup ###")
        print("Database Name? (default: nadinedb)")
        db_name = raw_input(PROMPT).strip()
        if not db_name:
            db_name = "nadinedb"
        print("DATABASE_NAME = '%s'" % db_name)
        print("Database User? (default: %s)" % current_user)
        db_user = raw_input(PROMPT).strip()
        if not db_user:
            db_user = current_user
        print("DATABASE_USER = '%s'" % db_user)
        print("Database Password? (optional)")
        db_pass = raw_input(PROMPT).strip()
        if db_pass:
            print("DATABASE_PASSWORD = '%s'" % db_pass)
        self.local_settings.set_database(db_name, db_user, db_pass)

        #print ("Migrating database")
        #from django.conf import settings
        #from django.core import management
        #management.call_command("migrate")

    def setup_admin(self):
        # TODO - doesn't work yet
        print("We need to create an administrator.")
        print("Admin First Name?")
        admin_first_name = raw_input(PROMPT).strip().title()
        print("Admin Last Name?")
        admin_last_name = raw_input(PROMPT).strip().title()
        print("Admin Email Address?")
        admin_email = raw_input(PROMPT).strip().lower()
        print("Admin Password?")
        admin_password = raw_input(PROMPT).strip()
        admin_username = "%s_%s" % (admin_first_name.lower(), admin_last_name.lower())
        admin_user = User.objects.create_superuser(admin_username, admin_email, admin_password)
        admin_user.first_name = admin_first_name
        admin_user.last_name = admin_last_name
        #print(admin_username)
        admin_user.save()

    # Mail Server Setup
    def setup_email(self):
        pass


class LocalSettings():

    def __init__(self, filename):
        print("Loading %s" % filename)
        with open(filename) as f:
            self.settings = f.readlines()

        self.settings.append("\n# Settings Generated by ./manage.py setup\n")

    def get_line_number(self, key):
        for i, line in enumerate(self.settings):
            if line.startswith(key):
                return i
        return -1

    def get(self, key):
        line_number = self.get_line_number(key)
        if line_number > 0:
            return self.settings[line_number]
        return None

    def set(self, key, value, quiet=False):
        new_line = '%s = "%s"\n' % (key, value)
        if not quiet:
            print(new_line)
        line_number = self.get_line_number(key)
        if line_number >= 0:
            self.settings[line_number] = new_line
        else:
            self.settings.append(new_line)

    def set_database(self, db_name=None, db_user=None, db_pass=None):
        self.settings.append("DATABASES = {\n")
        self.settings.append("    'default': {\n")
        self.settings.append("        'ENGINE': 'django.db.backends.postgresql_psycopg2',\n")
        if db_name:
            self.settings.append("         'NAME': '%s',\n" % db_name)
        if db_user:
            self.settings.append("         'USER': '%s',\n" % db_user)
        if db_pass:
            self.settings.append("         'PASSWORD': '%s',\n" % db_pass)
        self.settings.append("    }\n}\n")

    def save(self, filename):
        print("Writing new settings file...")
        with open(filename, 'w') as f:
            f.writelines(self.settings)
