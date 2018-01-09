from django.db import models
from django.conf import settings

class LDAPAccountStatus(models.Model):
    """
    Model to keep track of individual LDAP failures in Django's database.
    There's likely potential for a race condition here but I figure it's just
    for reporting and therefore fairly innocuous - better than nothing.

    TODO: This needs to be renamed to something a little less confusing.
    """
    objects = models.Manager()

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        primary_key=True,
        on_delete=models.CASCADE
    )
    has_error = models.BooleanField(default=False)
    last_error = models.CharField(max_length=255, blank=True)
    ldap_dn = models.CharField(unique=True, max_length=255, blank=True, null=True)