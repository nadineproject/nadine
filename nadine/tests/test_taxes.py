import unittest
from django.test import TestCase, override_settings

from django.contrib.auth.models import User

from decimal import Decimal
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from nadine.models.billing import BillingBatch, UserBill, TaxRate, LineItemTax
from nadine.models.membership import IndividualMembership, ResourceSubscription
from nadine.models.resource import ResourceManager, Resource

from ._test_helpers import create, a_subscriptionlineitem, a_coworkingdaylineitem, an_eventlineitem

from django.utils.timezone import localtime, now
today = localtime(now()).date()
one_month = relativedelta(month=1)
one_hour = timedelta(hours=1)

@override_settings(SUSPEND_MEMBER_ALERTS=True)
class TaxLineItemTestCase(TestCase):

    def setUp(self):
        # Ensure resources exist.
        day,_ = Resource.objects.get_or_create(key=Resource.objects.DAY_KEY, defaults={'name': 'Coworking Day', 'default_rate': 30})
        event,_ = Resource.objects.get_or_create(key=Resource.objects.EVENT_KEY, defaults={'name': 'Event Hours', 'default_rate': 10})
        key,_ = Resource.objects.get_or_create(key=Resource.objects.KEY_KEY, defaults={'name': 'Key', 'default_rate': 2})
        # Create some taxes.
        TaxRate.objects.get_or_create(name="GST", percentage=0.05)
        TaxRate.objects.get_or_create(name="PST", percentage=0.07)
        # Load taxes from db to avoid floating point insanity.
        self.gst,_ = TaxRate.objects.get_or_create(name="GST")
        self.pst,_ = TaxRate.objects.get_or_create(name="PST")
        # Apply taxes to resources.
        self.gst.resources.add(day, event, key)
        self.pst.resources.add(key)

        # Prepare a user, membership and subscription.
        self.user,_ = User.objects.get_or_create(username='test_user', first_name='Testy', last_name='Tester')
        self.membership,_ = IndividualMembership.objects.get_or_create(user=self.user)
        # Open a bill and add the subscription.
        self.bill = UserBill.objects.get_or_create_open_bill(
            self.user,
            period_start=today,
            period_end=today + one_month
        )

    def test_userbill_total_tax_applied_by_rate_calculates_totals_for_each_rate(self):
        """
        UserBill.calculate_taxes calculates the amount of tax charged for each
        tax rate.
        Returns a list of tuples of the form (rate<TaxRate>, total<Decimal>).
        """
        coworkingdaylineitem = create(a_coworkingdaylineitem(
            self.bill, self.user,
            amount=50
        ))
        line_item_taxes = coworkingdaylineitem.calculate_taxes()
        self.bill.add_lineitem_taxes(line_item_taxes)

        subscriptionlineitem = create(a_subscriptionlineitem(
            self.bill, self.membership,
            resource=Resource.objects.key_resource, amount=100
        ))
        line_item_taxes = subscriptionlineitem.calculate_taxes()
        self.bill.add_lineitem_taxes(line_item_taxes)

        taxes = self.bill.total_tax_applied_by_rate()
        self.assertEqual(len(taxes), 2, "One total per applied tax rate")

    @unittest.skip("Not implemented")
    def test_userbill_calculate_taxes(self):
        self.fail()

    def test_userbill_add_lineitem_taxes(self):
        """
        UserBill.add_lineitem_taxes() applies TaxLineItems to bill (persists
        them to database).
        """
        # Key resource has two taxes.
        subscriptionlineitem = create(a_subscriptionlineitem(
            self.bill, self.membership,
            resource=Resource.objects.key_resource, amount=100
        ))
        line_item_taxes = subscriptionlineitem.calculate_taxes()
        self.bill.add_lineitem_taxes(line_item_taxes)
        self.assertEqual(list(subscriptionlineitem.lineitemtax_set.all()), line_item_taxes)

        coworkingdaylineitem = create(a_coworkingdaylineitem(
            self.bill, self.user,
            amount=50
        ))
        line_item_taxes = coworkingdaylineitem.calculate_taxes()
        self.bill.add_lineitem_taxes(line_item_taxes)
        self.assertEqual(list(coworkingdaylineitem.lineitemtax_set.all()), line_item_taxes)

        eventlineitem = create(an_eventlineitem(
            self.bill, self.user,
            start_ts=today, end_ts=today + one_hour, amount=200
        ))
        line_item_taxes = eventlineitem.calculate_taxes()
        self.bill.add_lineitem_taxes(line_item_taxes)
        self.assertEqual(list(eventlineitem.lineitemtax_set.all()), line_item_taxes)

    def test_userbill_total_tax_applied_calculates_total_tax_applied_to_bill(self):
        """
        Calculates the sum of all applied LineItemTax amounts.
        """
        total = 0

        amount = 20
        line_item_taxes = create(a_subscriptionlineitem(
                self.bill, self.membership,
                resource=Resource.objects.key_resource, amount=amount
            )) \
            .calculate_taxes()
        for lineitem_tax in line_item_taxes:
            lineitem_tax.save()
        total += (amount * self.gst.percentage) + (amount * self.pst.percentage)

        amount = 50
        line_item_taxes = create(a_coworkingdaylineitem(
                self.bill, self.user,
                amount=amount
            )) \
            .calculate_taxes()
        for lineitem_tax in line_item_taxes:
            lineitem_tax.save()
        total += amount * self.gst.percentage

        self.assertEqual(self.bill.total_tax_applied(), total)
        self.assertEqual(self.bill.tax_amount, total)

    def test_billlineitem_calculate_taxes_applies_correct_taxrates(self):
        """
        BillLineItem.calculate_taxes creates one LineItemTax for each TaxRate
        that applies to the BillingLineItem's associated resource
        """
        # Day resource has one tax.
        day = Resource.objects.day_resource
        # Key resource has two taxes.
        key = Resource.objects.key_resource

        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            resource=day, amount=100
        ))
        line_item_taxes = line_item.calculate_taxes()
        self.assertEqual(
            len(line_item_taxes), day.taxrate_set.count(),
            "There should be one LineItemTax for each TaxRate on the Subscription's resource"
        )
        self.assertTrue(any(tax.tax_rate == self.gst for tax in line_item_taxes))
        self.assertFalse(any(tax.tax_rate == self.pst for tax in line_item_taxes))

        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            resource=key, amount=100
        ))
        line_item_taxes = line_item.calculate_taxes()
        self.assertEqual(
            len(line_item_taxes), key.taxrate_set.count(),
             "There should be one LineItemTax for each TaxRate on the Subscription's resource"
        )
        self.assertTrue(any(tax.tax_rate == self.gst for tax in line_item_taxes))
        self.assertTrue(any(tax.tax_rate == self.pst for tax in line_item_taxes))

    def test_billlineitem_calulate_taxes_doesnt_double_charge(self):
        """
        BillLineItem.calculate_taxes should check to see if a LineItemTax exists
        for a TaxRate before creating a new one.
        """
        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            amount=100
        ))
        # Calculate and persist taxes to database.
        taxes = line_item.calculate_taxes()
        for tax in taxes:
            tax.save()

        self.assertEqual(
            len(line_item.calculate_taxes()), len(taxes),
            "Multiple calls shouldn't cause duplicate LineItemTax to be created"
        )

    def test_billlineitem_calculate_taxes_does_not_apply_tax_when_amount_zero(self):
        """
        A zero-value BillLineItem should not have taxes applied.
        """
        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            amount=0
        ))
        self.assertEqual(len(line_item.calculate_taxes()), 0)

    def test_billlineitem_calculate_tax_amount(self):
        """
        Given a rate, calculate amount of tax charged for a BillLineItem
        """
        amount = 100
        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            amount=amount
        ))
        self.assertEqual(line_item.calculate_tax_amount(self.gst), amount * self.gst.percentage)

    def test_billlineitem_get_applied_tax(self):
        """
        Given a TaxRate, BillLineItem.get_applied_tax returns an associated
        LineItemTax if one exists.
        """
        line_item = create(a_subscriptionlineitem(
            self.bill, self.membership,
            amount=100
        ))
        self.assertEqual(
            line_item.get_applied_tax(self.gst), None,
            "Return None when TaxRate hasn't been applied"
        )

        # Calculate and apply (persist taxes to database).
        line_item_tax = line_item.calculate_taxes()[0]
        line_item_tax.save()
        self.assertEqual(
            line_item.get_applied_tax(self.gst), line_item_tax,
            "Return LineItemTax when TaxRate has been applied"
        )