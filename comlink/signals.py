# -*- coding: utf-8 -*-
from django.dispatch import Signal, receiver

email_received = Signal(providing_args=["instance","attachments"])

@receiver(email_received)
def my_callback(sender, **kwargs):
    print("Email Received")
    print(kwargs)
