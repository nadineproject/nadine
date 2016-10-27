from django.db import models
from django.db.models import Q, Sum
from django.conf import settings
from django.contrib.auth.models import User

class MailMessge(models.Model):
    """An email as popped for a mailing list"""
    created_ts = models.DateTimeField(auto_now_add=True)
    sent_ts = models.DateTimeField()
    #mailing_list = models.ForeignKey(MailingList)
    raw_message = models.TextField(blank=True)
    to_address = models.EmailField()
    from_address = models.EmailField()
    subject = models.TextField(blank=True)
    body_text = models.TextField(blank=True, null=True)
    body_html = models.TextField(blank=True, null=True)

    sender = models.ForeignKey(User, blank=True, null=True, default=None)

    #STATES = (('raw', 'raw'), ('moderate', 'moderate'), ('send', 'send'), ('sent', 'sent'), ('reject', 'reject'))
    #state = models.CharField(max_length=10, choices=STATES, default='raw')


class MailingList(models.Model):
    """Represents both the user facing information about a mailing list and how to fetch the mail"""
    name = models.CharField(max_length=1024)
    description = models.TextField(blank=True)
    subject_prefix = models.CharField(max_length=1024, blank=True)
    is_opt_out = models.BooleanField(default=False, help_text='True if new users should be automatically enrolled')
    moderator_controlled = models.BooleanField(default=False, help_text='True if only the moderators can send mail to the list and can unsubscribe users.')
    email_address = models.EmailField()
    subscribers = models.ManyToManyField(User, blank=True, related_name='subscribed_mailing_lists')
    moderators = models.ManyToManyField(User, blank=True, related_name='moderated_mailing_lists', help_text='Users who will be sent moderation emails', limit_choices_to={'is_staff': True})
    throttle_limit = models.IntegerField(default=0, help_text='The number of recipients in 10 minutes this mailing list is limited to. Default is 0, which means no limit.')
