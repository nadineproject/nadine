import traceback
from datetime import datetime, timedelta, date

from django.test import TestCase, override_settings
from django.core import management
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from nadine.models import *


@override_settings(SUSPEND_MEMBER_ALERTS=True)
class ProfileTestCase(TestCase):

    def setUp(self):
        self.neighborhood1 = Neighborhood.objects.create(name="Beggar's Gulch")

        # Basic Packages = just days
        self.basicPackage = MembershipPackage.objects.create(name="Basic")
        SubscriptionDefault.objects.create(
            package = self.basicPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 50,
            allowance = 3,
            overage_rate = 20,
        )

        # PT-5 Package + Key + Mail
        self.pt5Package = MembershipPackage.objects.create(name="PT5")
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.day_resource,
            monthly_rate = 75,
            allowance = 5,
            overage_rate = 20,
        )
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.key_resource,
            monthly_rate = 100,
            allowance = 1,
            overage_rate = 0,
        )
        SubscriptionDefault.objects.create(
            package = self.pt5Package,
            resource = Resource.objects.mail_resource,
            monthly_rate = 35,
            allowance = 1,
            overage_rate = 0,
        )

        # Resident Package with a desk
        self.residentPackage = MembershipPackage.objects.create(name="Resident")
        SubscriptionDefault.objects.create(
            package = self.residentPackage,
            resource = Resource.objects.day_resource,
            monthly_rate = 0,
            allowance = 5,
            overage_rate = 20,
        )
        SubscriptionDefault.objects.create(
            package = self.residentPackage,
            resource = Resource.objects.desk_resource,
            monthly_rate = 475,
            allowance = 1,
            overage_rate = 0,
        )

        self.user1 = User.objects.create(username='member_one', first_name='Member', last_name='One')
        self.profile1 = self.user1.profile
        self.profile1.neighborhood = self.neighborhood1
        self.profile1.valid_billing = True
        self.profile1.save()
        # Basic from 2/26/2008 to 6/25/2010
        # Resident from 6/26/2010 to date
        self.user1.membership.set_to_package(self.basicPackage, start_date=date(2008, 2, 26), end_date=date(2010, 6, 25))
        self.user1.membership.set_to_package(self.residentPackage, start_date=date(2010, 6, 26))

        self.user2 = User.objects.create(username='member_two', first_name='Member', last_name='Two')
        self.profile2 = self.user2.profile
        # PT-5 since 1/1/2009
        self.user2.membership.set_to_package(self.pt5Package, start_date=date(2009, 1, 1))

        self.user3 = User.objects.create(username='member_three', first_name='Member', last_name='Three')
        self.profile3 = self.user3.profile
        self.profile3.neighborhood = self.neighborhood1
        self.profile3.save()
        # No subscriptions

        self.user4 = User.objects.create(username='member_four', first_name='Member', last_name='Four')
        self.profile4 = self.user4.profile
        self.profile4.neighborhood = self.neighborhood1
        self.profile4.save()
        # Was a PT-5 from 1/1/2009 to 1/1/2010
        self.user4.membership.set_to_package(self.pt5Package, start_date=date(2009, 1, 1), end_date=date(2010, 1, 1))

        self.user5 = User.objects.create(username='member_five', first_name='Member', last_name='Five')
        self.profile5 = self.user5.profile
        self.profile5.valid_billing = False
        self.profile5.save()
        # PT-5 from 1/1/2009, paid by User1
        self.user5.membership.set_to_package(self.pt5Package, start_date=date(2009, 1, 1), paid_by=self.user1)


    ############################################################################
    # Tests
    ############################################################################

    def test_active_subscriptions(self):
        # Resident membership has 2 resource subscriptions
        self.assertEqual(2, self.user1.profile.active_subscriptions().count())
        # Our PT-5 membership has 3 resource subscriptions
        self.assertEqual(3, self.user2.profile.active_subscriptions().count())
        # User3, and 4 have no subscriptions
        self.assertEqual(0, self.user3.profile.active_subscriptions().count())
        self.assertEqual(0, self.user4.profile.active_subscriptions().count())

    def test_by_package(self):
        self.assertTrue(self.user1 in User.helper.members_by_package(self.residentPackage))
        self.assertFalse(self.user1 in User.helper.members_by_package(self.basicPackage))
        self.assertTrue(self.user2 in User.helper.members_by_package(self.pt5Package))
        self.assertFalse(self.user2 in User.helper.members_by_package(self.residentPackage))

    def test_by_neighborhood(self):
        self.assertTrue(self.user1 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user2 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user3 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertFalse(self.user4 in User.helper.members_by_neighborhood(self.neighborhood1))
        self.assertTrue(self.user3 in User.helper.members_by_neighborhood(self.neighborhood1, active_only=False))
        self.assertTrue(self.user4 in User.helper.members_by_neighborhood(self.neighborhood1, active_only=False))

    def test_by_resource(self):
        # User1 has a desk
        self.assertTrue(self.user1 in User.helper.members_with_desks())
        self.assertFalse(self.user1 in User.helper.members_with_keys())
        # User2 has key and mail
        self.assertTrue(self.user2 in User.helper.members_with_keys())
        self.assertTrue(self.user2 in User.helper.members_with_mail())
        self.assertFalse(self.user2 in User.helper.members_with_desks())
        # User3 doesn't have any resources
        self.assertFalse(self.user3 in User.helper.members_with_keys())
        self.assertFalse(self.user3 in User.helper.members_with_mail())
        self.assertFalse(self.user3 in User.helper.members_with_desks())
        # User4 doesn't have any resources
        self.assertFalse(self.user4 in User.helper.members_with_keys())
        self.assertFalse(self.user4 in User.helper.members_with_mail())
        self.assertFalse(self.user4 in User.helper.members_with_desks())
        # User5 has key and mail
        self.assertTrue(self.user5 in User.helper.members_with_keys())
        self.assertTrue(self.user5 in User.helper.members_with_mail())
        self.assertFalse(self.user5 in User.helper.members_with_desks())

    def test_valid_billing(self):
        # Member 1 has valid billing
        self.assertTrue(self.user1.profile.valid_billing)
        self.assertTrue(self.user1.profile.has_valid_billing())
        # Member 2 does not have valid billing
        self.assertFalse(self.user2.profile.valid_billing)
        self.assertFalse(self.user2.profile.has_valid_billing())
        # Member 5 does not have valid billing but is a guest of Member 1
        self.assertFalse(self.user5.profile.valid_billing)
        self.assertTrue(self.user5.profile.has_valid_billing())

    def test_is_guest(self):
        self.assertFalse(self.user1.profile.is_guest())
        self.assertFalse(self.user2.profile.is_guest())
        self.assertFalse(self.user3.profile.is_guest())
        self.assertFalse(self.user4.profile.is_guest())
        self.assertTrue(self.user5.profile.is_guest())

    def test_guests(self):
        guests = self.user1.profile.guests()
        self.assertEqual(1, len(guests))
        self.assertTrue(self.user5 in guests)
        self.assertEqual(0, len(self.user2.profile.guests()))
        self.assertEqual(0, len(self.user3.profile.guests()))
        self.assertEqual(0, len(self.user4.profile.guests()))
        self.assertEqual(0, len(self.user5.profile.guests()))

    def test_hosts(self):
        hosts = self.user5.profile.hosts()
        self.assertEqual(1, len(hosts))
        self.assertTrue(self.user1 in hosts)
        self.assertEqual(0, len(self.user1.profile.hosts()))
        self.assertEqual(0, len(self.user2.profile.hosts()))
        self.assertEqual(0, len(self.user3.profile.hosts()))
        self.assertEqual(0, len(self.user4.profile.hosts()))

    def test_tags(self):
        self.user1.profile.tags.add('coworking', 'books', 'beer')
        self.user2.profile.tags.add('beer', 'cars', 'women')
        self.user3.profile.tags.add('knitting', 'beer', 'travel')
        self.assertTrue(self.user1.profile in UserProfile.objects.filter(tags__name__in=['beer']))
        self.assertTrue(self.user2.profile in UserProfile.objects.filter(tags__name__in=['beer']))
        self.assertTrue(self.user3.profile in UserProfile.objects.filter(tags__name__in=['beer']))
        self.assertFalse(self.user1.profile in UserProfile.objects.filter(tags__name__in=['knitting']))
        self.assertFalse(self.user3.profile in UserProfile.objects.filter(tags__name__in=['books']))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
