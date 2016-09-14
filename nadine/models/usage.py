from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from nadine.models.resource import Room

import logging

logger = logging.getLogger(__name__)


class Event(models.Model):
    user = models.ForeignKey(User)
    room = models.ForeignKey(Room, null=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    start_ts = models.DateTimeField(verbose_name="Start time")
    end_ts = models.DateTimeField(verbose_name="End time")
    description = models.CharField(max_length=128, null=True)
    charge = models.DecimalField(decimal_places=2, max_digits=9)
    is_public = models.BooleanField(default=False)

    def __unicode__(self):
        if self.description:
            return self.description
        if self.is_public:
            return "Public Event (%s)" % user.get_full_name()
        return "Private Event (%s)" % user.get_full_name()
