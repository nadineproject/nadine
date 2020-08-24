import logging

from django.dispatch import Signal

logger = logging.getLogger(__name__)

new_membership = Signal(providing_args=["user"])
ending_membership = Signal(providing_args=["user"])
changing_membership_password = Signal(providing_args=["user", "password"])


class MemberAlertManager:

    def handle_new_membership(self, _user):
        logger.debug("handle_new_membership: %s" % _user.username)
        new_membership.send(sender=self, user=_user)

    def handle_ending_membership(self, _user):
        logger.debug("handle_ending_membership: %s" % _user.username)
        ending_membership.send(sender=self, user=_user)

    def handle_changing_membership_password(self, _user, _pass):
        logger.debug("handle_changing_membership_password: %s" % _user.username)
        changing_membership_password.send(sender=self, user=_user, password=_pass)
