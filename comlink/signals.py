# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver
from django.contrib.auth.models import User
from django.conf import settings

from nadine.utils import mailgun

email_received = Signal(providing_args=["instance", "attachments"])

@receiver(email_received)
def router(sender, **kwargs):
    # Pull our email object and convert it to the mailgun_data we need`
    email = kwargs['instance']
    mailgun_data = email.get_mailgun_data(stripped=True, footer=True)

    # Pull our attachments and convert it to the list of files we need
    attachments = kwargs['attachments']
    files = []
    for a in attachments:
        files.append(('attachment', open(a.file.path)))

    # Build out the BCC depending on who the recipient is
    if email.recipient == 'staff@test.officenomads.com':
        mailgun_data["bcc"] = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
    elif email.recipient == 'team@test.officenomads.com':
        mailgun_data["bcc"] = list(User.helper.managers(include_future=True).values_list('email', flat=True))
    else:
        # Nothing to see here... move along...
        return

    # Pass this message along
    mailgun.mailgun_send(mailgun_data, files)
