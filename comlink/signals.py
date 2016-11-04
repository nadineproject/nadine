# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver
from django.contrib.auth.models import User
from django.conf import settings

from nadine.utils import mailgun

email_received = Signal(providing_args=["instance", "attachments"])

def staff_email(email, attachments):
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)
    mailgun_data["bcc"] = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
    #mailgun_data["to"] = mailgun_data["to"].insert(0, "staff@%s" % settings.MAILGUN_DOMAIN)
    return mailgun.mailgun_send(mailgun_data, attachments)

def team_email(email, attachments):
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)
    mailgun_data["bcc"] = list(User.helper.managers(include_future=True).values_list('email', flat=True))
    #mailgun_data["to"] = mailgun_data["to"].insert(0, "team@%s" % settings.MAILGUN_DOMAIN)
    return mailgun_send(mailgun_data, attachments)

routes = [
    ('staff@test.officenomads.com', staff_email),
    ('team@test.officenomads.com', team_email),
]

@receiver(email_received)
def router(sender, **kwargs):
    incoming_email = kwargs['instance']
    attachments = kwargs['attachments']
    for r, f in routes:
        if incoming_email.recipient == r:
            return f(incoming_email, attachments)
    raise RejectedMailException("No route found!")
