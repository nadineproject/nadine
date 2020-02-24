from django.db import models
from django.db.models import Q, Sum
from django.conf import settings
from django.contrib.auth.models import User

# class MailMessge(models.Model):
#     """An email as popped for a mailing list"""
#     created_ts = models.DateTimeField(auto_now_add=True)
#     sent_ts = models.DateTimeField()
#     #mailing_list = models.ForeignKey(MailingList, on_delete=models.CASCADE)
#     raw_message = models.TextField(blank=True)
#     to_address = models.EmailField()
#     from_address = models.EmailField()
#     subject = models.TextField(blank=True)
#     body_text = models.TextField(blank=True, null=True)
#     body_html = models.TextField(blank=True, null=True)
#
#     sender = models.ForeignKey(User, blank=True, null=True, default=None, on_delete=models.CASCADE)
#
#     #STATES = (('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject'))
#     #state = models.CharField(max_length=10, choices=STATES, default='raw')
#
#
# class MailingList(models.Model):
#     """Represents both the user facing information about a mailing list and how to fetch the mail"""
#     name = models.CharField(max_length=1024)
#     description = models.TextField(blank=True)
#     subject_prefix = models.CharField(max_length=1024, blank=True)
#     is_opt_out = models.BooleanField(default=False, help_text='True if new users should be automatically enrolled')
#     moderator_controlled = models.BooleanField(default=False, help_text='True if only the moderators can send mail to the list and can unsubscribe users.')
#     email_address = models.EmailField()
#     subscribers = models.ManyToManyField(User, blank=True, related_name='subscribed_mailing_lists')
#     moderators = models.ManyToManyField(User, blank=True, related_name='moderated_mailing_lists', help_text='Users who will be sent moderation emails', limit_choices_to={'is_staff': True})
#     throttle_limit = models.IntegerField(default=0, help_text='The number of recipients in 10 minutes this mailing list is limited to. Default is 0, which means no limit.')

# Not ready yet.  This was pulled in from modernomads. --JLS
# Keys need to be updated to keys in nadine.email.py

# class EmailTemplate(models.Model):
#     ''' Template overrides for system generated emails '''
#
#     ADMIN_DAILY = 'admin_daily_update'
#     GUEST_DAILY = 'guest_daily_update'
#     INVOICE = 'invoice'
#     RECEIPT = 'receipt'
#     SUBSCRIPTION_RECEIPT = 'subscription_receipt'
#     NEW_RESERVATION = 'newreservation'
#     WELCOME = 'pre_arrival_welcome'
#     DEPARTURE = 'departure'
#
#     KEYS = (
#     (ADMIN_DAILY, 'Admin Daily Update'),
#     (GUEST_DAILY, 'Guest Daily Update'),
#     (INVOICE, 'Invoice'),
#     (RECEIPT, 'Reservation Receipt'),
#     (SUBSCRIPTION_RECEIPT, 'Subscription Receipt'),
#     (NEW_RESERVATION, 'New Reservation'),
#     (WELCOME, 'Pre-Arrival Welcome'),
#     (DEPARTURE, 'Departure'),
#     )
#
#     key = models.CharField(max_length=32, choices=KEYS)
#     text_body = models.TextField(verbose_name="The text body of the email")
#     html_body = models.TextField(blank=True, null=True, verbose_name="The html body of the email")


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
