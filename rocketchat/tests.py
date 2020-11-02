from django.test import TestCase
from django.contrib.auth.models import User

from unittest.mock import patch

from .models.alerts import MemberAlertManager
from .signals import randomStringDigits

import logging

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)


class RocketchatTestCase(TestCase):

    myClass = MemberAlertManager()
    _pass = randomStringDigits()

    def setUp(self):
        self._usr = User.objects.create_user('4321_test_1234', email='test@example.com', password='password')

    def tearDown(self):
        self._usr.delete()

    @patch('rocketchat.signals.logger')
    def test_adding_rocketchat_user(self, mock_logger):
        self.myClass.handle_new_membership(self._usr)
        mock_logger.debug.assert_called_with('Adding user %s success' % self._usr.username)
        _logger.debug('test_adding_nexcloud_user %s success' % self._usr.username)

    @patch('rocketchat.signals.logger')
    def test_changing_rocketchat_user_password(self, mock_logger):
        self.myClass.handle_changing_membership_password(self._usr, self._pass)
        mock_logger.debug.assert_called_with('Changing user %s password success' % self._usr.username)
        _logger.debug('test_changing_nexcloud_user_password %s success' % self._usr)

    @patch('rocketchat.signals.logger')
    def test_removing_rocketchat_user(self, mock_logger):
        self.myClass.handle_ending_membership(self._usr)
        mock_logger.debug.assert_called_with('Removing user %s success' % self._usr.username)
        _logger.debug('test_removing_nexcloud_user %s success' % self._usr)
