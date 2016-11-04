# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver
from django.contrib.auth.models import User
from django.conf import settings

from nadine import mailgun

email_received = Signal(providing_args=["instance", "attachments"])

def staff_email(email, attachments):
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)

    # Pull the list this should go to and set them in the BCC
    # Going out to all Users that are active and staff
    bcc_list = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
    mailgun_data["bcc"] = bcc_list

    # This goes out to staff and anyone that isn't already in the BCC list
    to_list = ["staff@%s" % settings.MAILGUN_DOMAIN, ]
    for to in mailgun_data["to"]:
        if not to in bcc_list:
            to_list.append(to)
    mailgun_data["to"] = to_list

    # Send the message
    return mailgun.mailgun_send(mailgun_data, attachments)


def team_email(email, attachments):
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)

    # Goes out to all managers
    bcc_list = list(User.helper.managers(include_future=True).values_list('email', flat=True))
    mailgun_data["bcc"] = bcc_list

    # Hard code the recipient to be this address
    to_list = ["team@%s" % settings.MAILGUN_DOMAIN, ]
    for to in mailgun_data["to"]:
        if not to in bcc_list:
            to_list.append(to)
    mailgun_data["to"] = to_list

    # Send the message
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
