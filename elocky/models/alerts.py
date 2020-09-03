import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

new_membership = Signal(providing_args=["user"])
ending_membership = Signal(providing_args=["user"])


class MemberAlertManager:

    def handle_new_membership(self, _user):
        logger.debug("handle_new_membership: %s" % _user.username)
        new_membership.send(sender=self, user=_user)

    def handle_ending_membership(self, _user):
        logger.debug("handle_ending_membership: %s" % _user.username)
        ending_membership.send(sender=self, user=_user)

