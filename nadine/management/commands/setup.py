import os
import string
import random
import getpass
import socket
import zoneinfo

from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.core.management.utils import get_random_secret_key


EXAMPLE_LOCAL_SETTINGS_FILE = "nadine/settings/local_settings.example.py"
LOCAL_SETTINGS_FILE = "nadine/settings/local_settings.py"
PROMPT = '> '

COUNTRIES = [
    "AF", "AX", "AL", "DZ", "AS", "AD", "AO", "AI", "AQ", "AG", "AR",
    "AM", "AW", "AU", "AT", "AZ", "BS", "BH", "BD", "BB", "BY", "BE",
    "BZ", "BJ", "BM", "BT", "BO", "BQ", "BA", "BW", "BV", "BR", "IO",
    "BN", "BG", "BF", "BI", "CV", "KH", "CM", "CA", "KY", "CF", "TD",
    "CL", "CN", "CX", "CC", "CO", "KM", "CG", "CD", "CK", "CR", "CI",
    "HR", "CU", "CW", "CY", "CZ", "DK", "DJ", "DM", "DO", "EC", "EG",
    "SV", "GQ", "ER", "EE", "ET", "FK", "FO", "FJ", "FI", "FR", "GF",
    "PF", "TF", "GA", "GM", "GE", "DE", "GH", "GI", "GR", "GL", "GD",
    "GP", "GU", "GT", "GG", "GN", "GW", "GY", "HT", "HM", "VA", "HN",
    "HK", "HU", "IS", "IN", "ID", "IR", "IQ", "IE", "IM", "IL", "IT",
    "JM", "JP", "JE", "JO", "KZ", "KE", "KI", "KP", "KR", "KW", "KG",
    "LA", "LV", "LB", "LS", "LR", "LY", "LI", "LT", "LU", "MO", "MK",
    "MG", "MW", "MY", "MV", "ML", "MT", "MH", "MQ", "MR", "MU", "YT",
    "MX", "FM", "MD", "MC", "MN", "ME", "MS", "MA", "MZ", "MM", "NA",
    "NR", "NP", "NL", "NC", "NZ", "NI", "NE", "NG", "NU", "NF", "MP",
    "NO", "OM", "PK", "PW", "PS", "PA", "PG", "PY", "PE", "PH", "PN",
    "PL", "PT", "PR", "QA", "RE", "RO", "RU", "RW", "BL", "SH", "KN",
    "LC", "MF", "PM", "VC", "WS", "SM", "ST", "SA", "SN", "RS", "SC",
    "SL", "SG", "SX", "SK", "SI", "SB", "SO", "ZA", "GS", "SS", "ES",
    "LK", "SD", "SR", "SJ", "SZ", "SE", "CH", "SY", "TW", "TJ", "TZ",
    "TH", "TL", "TG", "TK", "TO", "TT", "TN", "TR", "TM", "TC", "TV",
    "UG", "UA", "AE", "GB", "US", "UM", "UY", "UZ", "VU", "VE", "VN",
    "VG", "VI", "WF", "EH", "YE", "ZM", "ZW"
]


class Command(BaseCommand):
    help = "System Setup"
    requires_system_checks = False

    def handle(self, *args, **options):
        try:
            print()
            print("###################################")
            print("Nadine Local Settings Configuration")
            print("###################################")
            print()
            self.load_settings_file()
            self.setup_general()
            self.setup_timezone()
            self.setup_email()
            self.setup_database()
            self.setup_nextcloud()
            self.setup_rocketchat()
            self.setup_elocky()
            self.write_settings_file()
        except KeyboardInterrupt:
            print()
            print("Exiting without saving!")
            print()

    def load_settings_file(self):
        # Test to see if LOCAL_SETTINGS_FILE exists and prompt to load it or remove it
        filename = EXAMPLE_LOCAL_SETTINGS_FILE
        if os.path.isfile(LOCAL_SETTINGS_FILE):
            print(("File '%s' exists!" % LOCAL_SETTINGS_FILE))
            print("Do you want to load the existing file? (Y, n)")
            load = input(PROMPT).strip().lower()
            if load == "n":
                print(("Current settings in '%s' will be lost!" % LOCAL_SETTINGS_FILE))
            else:
                filename = LOCAL_SETTINGS_FILE
        self.local_settings = LocalSettings(filename)
        print()

    def write_settings_file(self):
        print("Write new local_settings file? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            print(("Writing %s" % LOCAL_SETTINGS_FILE))
            self.local_settings.save(LOCAL_SETTINGS_FILE)

    def prompt_for_value(self, question, key, default=None, can_none=False):
        if not default:
            default = self.local_settings.get_value(key)
        print(("%s? (default: '%s')" % (question, default)))
        value = input(PROMPT).strip().lower()
        if not value:
            value = default
        if can_none is True and value.strip().lower() == "none":
            self.local_settings.set(key, None, is_string=False)
            return
        self.local_settings.set(key, value)

    def setup_general(self):
        print("### General Settings ###")

        # Secret Key
        secret_key = self.local_settings.get("SECRET_KEY")
        if not secret_key or len(secret_key) < 32:
            print("Generating random SECRET_KEY")
            self.local_settings.set('SECRET_KEY', get_random_secret_key(), quiet=True)
            print()

        # Site Information
        self.prompt_for_value("Site Name", "SITE_NAME")
        self.prompt_for_value("Site Url", "SITE_URL")
        url = self.local_settings.get_value("SITE_URL")
        if url.endswith("/"):
            self.local_settings.set('SITE_URL', url[:-1])

        # Site Administrator
        print("Full Name of Administrator")
        admin_name = input(PROMPT).strip().title()
        print("Admin Email Address?")
        admin_email = input(PROMPT).strip().lower()
        self.local_settings.set_admins(admin_name, admin_email)

    def setup_timezone(self):
        print()
        print("### Timezone Setup ###")

        # Country
        country = ''
        while country not in COUNTRIES:
            print("What country? (blank: list available)")
            country = input(PROMPT).strip().upper()
            if not country:
                print("Country Codes:")
                print(", ".join(COUNTRIES))
                print()
        self.local_settings.set('COUNTRY', country)

        # Timezone
        tz = ''
        while tz not in zoneinfo.available_timezones():
            print("What timezone? (blank: list available)")
            tz = input(PROMPT).strip()
            if not tz:
                print("Available Timezones:")
                print((", ".join(zoneinfo.available_timezones())))
                print()
        self.local_settings.set('TIME_ZONE', tz)

    # Database Setup
    def setup_database(self):
        print()
        print("### Database Setup ###")
        print("Database Name? (default: nadinedb)")
        db_name = input(PROMPT).strip()
        if not db_name:
            db_name = "nadinedb"
        print(("DATABASE_NAME = '%s'" % db_name))
        current_user = getpass.getuser()
        print(("Database User? (default: %s)" % current_user))
        db_user = input(PROMPT).strip()
        if not db_user:
            db_user = current_user
        print(("DATABASE_USER = '%s'" % db_user))
        print("Database Password? (optional)")
        db_pass = input(PROMPT).strip()
        if db_pass:
            print(("DATABASE_PASSWORD = '%s'" % db_pass))
        self.local_settings.set_database(db_name, db_user, db_pass)

    # Mail Server Setup
    def setup_email(self):
        print()
        print("### Email Setup ###")
        domain = self.local_settings.get_value("SITE_URL").split('://')[1].split(':')[0].split('/')[0]
        self.prompt_for_value("Email Host", "EMAIL_HOST")
        self.prompt_for_value("Email Host User", "EMAIL_HOST_USER", default="postmaster@" + domain)
        self.prompt_for_value("Email Host Password", "EMAIL_HOST_PASSWORD")
        # self.prompt_for_value("Email Host Port", "EMAIL_PORT")
        # self.prompt_for_value("User TSL", "EMAIL_USE_TLS")
        self.prompt_for_value("Subject Prefix", "EMAIL_SUBJECT_PREFIX")
        self.prompt_for_value("Sent From Address", "DEFAULT_FROM_EMAIL", default="nadine@" + domain)
        default_from = self.local_settings.get_value("DEFAULT_FROM_EMAIL")
        self.local_settings.set('SERVER_EMAIL', default_from)
        self.prompt_for_value("Staff Address", "STAFF_EMAIL_ADDRESS", default="staff@" + domain)
        self.prompt_for_value("Billing Address", "BILLING_EMAIL_ADDRESS", default="billing@" + domain)
        self.prompt_for_value("Team Address", "TEAM_EMAIL_ADDRESS", default="team@" + domain)

    # Nextcloud Setup
    def setup_nextcloud(self):
        print()
        print("### Nextcloud Setup ###")
        print("Setup Nextcloud user provisioning? (y, N)")
        save = input(PROMPT).strip().lower()
        if save != "y":
            return
        self.local_settings.settings.append("INSTALLED_APPS += ['nextcloud']\n")
        self.prompt_for_value("Nextcloud Host", "NEXTCLOUD_HOST")
        self.prompt_for_value("Nextcloud Admin username", "NEXTCLOUD_ADMIN")
        self.prompt_for_value("Nextcloud Admin password", "NEXTCLOUD_PASSWORD")
        print("Use HTTPS connection? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("NEXTCLOUD_USE_HTTPS", True, is_string=False)
        else:
            self.local_settings.set("NEXTCLOUD_USE_HTTPS", False, is_string=False)
        print("SSL cert is signed? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("NEXTCLOUD_SSL_IS_SIGNED", True, is_string=False)
        else:
            self.local_settings.set("NEXTCLOUD_SSL_IS_SIGNED", False, is_string=False)
        self.prompt_for_value("Default user password (if None password will be randomised)", "NEXTCLOUD_USER_DEFAULT_PASSWORD", can_none=True)
        print("Send invitation password to new member by mail? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("NEXTCLOUD_USER_SEND_EMAIL_PASSWORD", True, is_string=False)
        else:
            self.local_settings.set("NEXTCLOUD_USER_SEND_EMAIL_PASSWORD", False, is_string=False)
        self.prompt_for_value("Add new user to group (optional)", "NEXTCLOUD_USER_GROUP", can_none=True)
        self.prompt_for_value("Nextcloud user quota", "NEXTCLOUD_USER_QUOTA")

    # Rocketchat Setup
    def setup_rocketchat(self):
        print()
        print("### Rocket.Chat Setup ###")
        print("Setup Rocket.Chat user provisioning? (y, N)")
        save = input(PROMPT).strip().lower()
        if save != "y":
            return
        self.local_settings.settings.append("INSTALLED_APPS += ['rocketchat']\n")
        self.prompt_for_value("Rocketchat Host", "ROCKETCHAT_HOST")
        self.prompt_for_value("Rocketchat Admin username", "ROCKETCHT_ADMIN")
        self.prompt_for_value("Rocketchat Admin password", "ROCKETCHAT_SECRET")
        print("Use HTTPS connection? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("ROCKETCHAT_USE_HTTPS", True, is_string=False)
        else:
            self.local_settings.set("ROCKETCHAT_USE_HTTPS", False, is_string=False)
        print("SSL cert is signed? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("ROCKETCHAT_SSL_IS_SIGNED", True, is_string=False)
        else:
            self.local_settings.set("ROCKETCHAT_SSL_IS_SIGNED", False, is_string=False)
        self.prompt_for_value("Default user password (if None password will be randomised)", "ROCKETCHAT_USER_DEFAULT_PASSWORD", can_none=True)
        print("Send welcome email to new member? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("ROCKETCHAT_SEND_WELCOME_MAIL", True, is_string=False)
        else:
            self.local_settings.set("ROCKETCHAT_SEND_WELCOME_MAIL", False, is_string=False)
        print("User should change password on login? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("ROCKETCHAT_REQUIRE_CHANGE_PASS", True, is_string=False)
        else:
            self.local_settings.set("ROCKETCHAT_REQUIRE_CHANGE_PASS", False, is_string=False)
        print("Verified user with her email address? (y, N)")
        save = input(PROMPT).strip().lower()
        if save == "y":
            self.local_settings.set("ROCKETCHAT_VERIFIED_USER", True, is_string=False)
        else:
            self.local_settings.set("ROCKETCHAT_VERIFIED_USER", False, is_string=False)
        print("Add user to rocketchat groups (split group with ',')? (default: None)")
        save = [x.strip() for x in input(PROMPT).split(',') if x.strip()]
        if not save:
            save = None
        self.local_settings.set("ROCKETCHAT_USER_GROUP", str(save), is_string=False)

    # Elocky Setup
    def setup_elocky(self):
        print()
        print("### Elocky Setup ###")
        print("Setup Elocky user provisioning? (y, N)")
        save = input(PROMPT).strip().lower()
        if save != "y":
            return
        self.local_settings.settings.append("INSTALLED_APPS += ['elocky']\n")
        cryptography_key = self.local_settings.get("CRYPTOGRAPHY_KEY")
        if not cryptography_key or len(cryptography_key) < 38:
            print("Generating random CRYPTOGRAPHY_KEY")
            self.local_settings.set('CRYPTOGRAPHY_KEY', get_random_secret_key(), quiet=True)
            print()
        self.prompt_for_value("Elocky API key client ID", "ELOCKY_API_CLIENT_ID")
        self.prompt_for_value("Elocky API key client SECRET", "ELOCKY_API_CLIENT_SECRET")
        self.prompt_for_value("Elocky Admin username", "ELOCKY_USERNAME")
        self.prompt_for_value("Elocky Admin password", "ELOCKY_PASSWORD")


class LocalSettings():

    def __init__(self, filename):
        print(("Loading %s" % filename))
        with open(filename) as f:
            self.settings = f.readlines()

        if not self.settings[0].startswith("# Generated using"):
            self.settings.insert(0, "# Generated using ./manage.py setup (%s)\n" % datetime.now())

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

    def get_value(self, key):
        value = self.get(key)
        if not value:
            return None
        clean_value = value[value.index('=') + 1:].strip()
        if clean_value[0] == "'" or clean_value[0] == '"':
            return clean_value[1:len(clean_value)-1]
        return clean_value

    def set(self, key, value, quiet=False, is_string=True):
        if is_string is False:
            new_line = '%s = %s\n' % (key, value)
        else:
            new_line = '%s = "%s"\n' % (key, value)
        if not quiet:
            print(new_line)
        line_number = self.get_line_number(key)
        if line_number >= 0:
            self.settings[line_number] = new_line
        else:
            self.settings.append(new_line)

    def set_admins(self, admin_name, admin_email):
        line_number = self.get_line_number("ADMINS")
        self.settings[line_number + 1] = "    ('%s', '%s')\n" % (admin_name, admin_email)

    def set_database(self, db_name, db_user, db_pass=None):
        line_number = self.get_line_number("DATABASES")
        self.settings[line_number + 2] = "        'NAME': '%s',\n" % db_name
        self.settings[line_number + 3] = "        'USER': '%s',\n" % db_user
        if db_pass:
            self.settings[line_number + 4] = "        'PASSWORD': '%s',\n" % db_pass
        else:
            self.settings[line_number + 4] = "        #'PASSWORD': 'password',\n"

    def save(self, filename):
        print("Writing new settings file...")
        with open(filename, 'w') as f:
            f.writelines(self.settings)


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
