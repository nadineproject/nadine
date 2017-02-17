# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 19:59
from __future__ import unicode_literals
from datetime import datetime, timedelta, date

from monthdelta import MonthDelta, monthmod

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def forward(apps, schema_editor):
    User = apps.get_model(settings.AUTH_USER_MODEL)
    OldBill = apps.get_model("nadine", "OldBill")
    Transaction = apps.get_model("nadine", "Transaction")
    UserBill = apps.get_model("nadine", "UserBill")
    BillLineItem = apps.get_model("nadine", "BillLineItem")
    CoworkingDayLineItem = apps.get_model("nadine", "CoworkingDayLineItem")
    Payment = apps.get_model("nadine", "Payment")
    print

    print("    Migrating Old Bills...")
    for o in OldBill.objects.all():
        # OldBill -> UserBill
        if o.paid_by:
            user = o.paid_by
        else:
            user = o.user
        start = o.bill_date
        end = start + MonthDelta(1) - timedelta(days=1)
        bill = UserBill.objects.create(
            user = user,
            period_start = start,
            period_end = end,
        )

        # We'll just create one line item for these old bills
        line_item = CoworkingDayLineItem.objects.create(
            bill = bill,
            description = "Coworking Membership",
            amount = o.amount,
            custom = True,
        )

        # Add all the dropins and guest dropins
        for d in o.dropins.all():
            line_item.days.add(d)
        for d in o.guest_dropins.all():
            line_item.days.add(d)
        line_item.save()
        bill.save()

        # Transactions -> Payments
        for t in o.transactions.all():
            Payment.objects.create(
                bill = bill,
                user = user,
                payment_date = t.transaction_date,
                paid_amount = t.amount,
            )

            # Move transaction notes to bill comments
            if t.note:
                comment = ""
                if bill.comment:
                    comment = bill.comment
                comment += t.note
                bill.comment = comment
                bill.save()


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('nadine', '0029_old_bill'),
    ]

    operations = [
        migrations.CreateModel(
            name='BillLineItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=200)),
                ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('custom', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_date', models.DateTimeField(auto_now_add=True)),
                ('payment_service', models.CharField(blank=True, help_text=b'e.g., Stripe, Paypal, Dwolla, etc. May be empty', max_length=200, null=True)),
                ('payment_method', models.CharField(blank=True, help_text=b'e.g., Visa, cash, bank transfer', max_length=200, null=True)),
                ('paid_amount', models.DecimalField(decimal_places=2, default=0, max_digits=7)),
                ('transaction_id', models.CharField(blank=True, max_length=200, null=True)),
                ('last4', models.IntegerField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='UserBill',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('generated_on', models.DateTimeField(auto_now=True)),
                ('period_start', models.DateField()),
                ('period_end', models.DateField()),
                ('comment', models.TextField(blank=True, null=True)),
                ('in_progress', models.BooleanField(default=False)),
                # ('membership', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='nadine.Membership')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bill', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CoworkingDayLineItem',
            fields=[
                ('billlineitem_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='nadine.BillLineItem')),
                ('days', models.ManyToManyField(related_name='bill_line', to='nadine.CoworkingDay')),
            ],
            bases=('nadine.billlineitem',),
        ),
        migrations.AddField(
            model_name='payment',
            name='bill',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='nadine.UserBill'),
        ),
        migrations.AddField(
            model_name='payment',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='billlineitem',
            name='bill',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='line_items', to='nadine.UserBill'),
        ),

        # Convert all the old bills to new ones
        migrations.RunPython(forward, reverse),

    ]