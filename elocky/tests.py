from django.test import TestCase
from django.contrib.auth.models import User

from unittest.mock import patch

from elocky.models.alerts import MemberAlertManager
from elocky.models.elocky_cred import ElockyCred

import logging

logging.basicConfig(level=logging.DEBUG)

_logger = logging.getLogger(__name__)


class ElockyTestCase(TestCase):
    myClass = MemberAlertManager()

    def setUp(self):
        self._usr = User.objects.create_user('4321_test_1234', email='test@example.com', password='password')

    def tearDown(self):
        self._usr.delete()

    @patch('elocky.signals.logger')
    def test_adding_elocky_user(self, mock_logger):
        self.myClass.handle_new_membership(self._usr)
        mock_logger.debug.assert_called_with('Adding user %s success' % self._usr.username)
        _logger.debug('test_adding_elocky_user %s success' % self._usr.username)

    @patch('elocky.signals.logger')
    def test_removing_elocky_user(self, mock_logger):
        self.myClass.handle_ending_membership(self._usr)
        mock_logger.debug.assert_called_with('Removing user %s success' % self._usr.username)
        _logger.debug('test_removing_elocky_user %s success' % self._usr)
