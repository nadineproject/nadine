# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver

email_received = Signal(providing_args=["instance", "attachments"])

class forward(object):

    def __init__(self, email, attachments):
        self.f = f

    def __call__(self):
        print "Entering", self.f.__name__
        self.f()
        print "Exited", self.f.__name__

def staff_email(email, attachments):
    print("Staff")
    pass

def team_email(email, attachments):
    print("Team")
    pass

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
