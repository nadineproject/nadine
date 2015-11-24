from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.utils import timezone
from taggit.forms import *

from nadine.models.core import *
from nadine.models.payment import *
from staff import usaepay
from staff import email

import datetime
import logging

logger = logging.getLogger(__name__)


class DateRangeForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()


class PayBillsForm(forms.Form):
    member_id = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)
    amount = forms.DecimalField(min_value=0, max_value=10000, required=True, max_digits=7, decimal_places=2)
    transaction_note = forms.CharField(required=False, widget=forms.Textarea)


class RunBillingForm(forms.Form):
    run_billing = forms.BooleanField(required=True, widget=forms.HiddenInput)


class NewUserForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="First name *", required=True, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    last_name = forms.CharField(max_length=100, label="Last name *", required=True, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    email = forms.EmailField(max_length=100, label="Email *", required=True)
    #phone = forms.CharField(max_length=100, required=False)

    def save(self):
        "Creates the User and Member records with the field data and returns the user"
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        first = self.cleaned_data['first_name'].strip().title()
        if len(first) == 0:
            raise forms.ValidationError("First Name Required.")
        last = self.cleaned_data['last_name'].strip().title()
        if len(last) == 0:
            raise forms.ValidationError("Last Name Required.")
        email = self.cleaned_data['email'].strip().lower()
        if len(email) == 0:
            raise forms.ValidationError("Email Required.")
        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("Email address '%s' already in use." % email)
        username = "%s_%s" % (first.lower(), last.lower())
        if User.objects.filter(username=username).count() > 0:
            raise forms.ValidationError("Username '%s' already in use." % username)

        user = User(username=username, first_name=first, last_name=last, email=email)
        password = User.objects.make_random_password(length=32)
        user.set_password(password)
        user.save()
        #member = user.get_profile()
        #member.phone = self.cleaned_data['phone'].strip()
        # member.save()

        return user

    class Meta:
        widgets = {
            'first_name': forms.TextInput(attrs={'autocapitalize': 'on', 'autocorrect': 'off'}),
            'last_name': forms.TextInput(attrs={'autocapitalize': 'on', 'autocorrect': 'off'}),
        }


class MemberSearchForm(forms.Form):
    terms = forms.CharField(max_length=100)


class MemberEditForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    first_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}))
    last_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}))
    email = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}))
    email2 = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    phone = forms.CharField(widget=forms.TextInput(attrs={'size': '16'}), required=False)
    phone2 = forms.CharField(widget=forms.TextInput(attrs={'size': '16'}), required=False)
    address1 = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    address2 = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    city = forms.CharField(widget=forms.TextInput(attrs={'size': '20'}), required=False)
    state = forms.CharField(widget=forms.TextInput(attrs={'size': '5'}), required=False)
    zipcode = forms.CharField(widget=forms.TextInput(attrs={'size': '10'}), required=False)
    company_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_personal = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_professional = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_facebook = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_twitter = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_linkedin = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_github = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    url_aboutme = forms.URLField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
    howHeard = forms.ModelChoiceField(label="How heard", queryset=HowHeard.objects.all(), required=False)
    industry = forms.ModelChoiceField(queryset=Industry.objects.all(), required=False)
    neighborhood = forms.ModelChoiceField(queryset=Neighborhood.objects.all(), required=False)
    has_kids = forms.NullBooleanField(required=False)
    self_employed = forms.NullBooleanField(required=False)
    photo = forms.ImageField(required=False)

    emergency_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Emergency Contact", required=False)
    emergency_relationship = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Relationship", required=False)
    emergency_phone = forms.CharField(widget=forms.TextInput(attrs={'size': '16'}), label="Phone", required=False)
    emergency_email = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), label="E-mail", required=False)
    
    def save(self):
        "Creates the User and Member records with the field data and returns the user"
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        user = User.objects.get(username=self.cleaned_data['username'])

        print self.cleaned_data
        
        user.first_name=self.cleaned_data['first_name']
        user.last_name=self.cleaned_data['last_name']
        user.email=self.cleaned_data['email']
        user.save()

        profile = user.get_profile()
        profile.email2 = self.cleaned_data['email2']
        profile.phone = self.cleaned_data['phone']
        profile.phone2 = self.cleaned_data['phone2']
        profile.address1 = self.cleaned_data['address1']
        profile.address2 = self.cleaned_data['address2']
        profile.city = self.cleaned_data['city']
        profile.state = self.cleaned_data['state']
        profile.zipcode = self.cleaned_data['zipcode']
        profile.url_personal = self.cleaned_data['url_personal']
        profile.url_professional = self.cleaned_data['url_professional']
        profile.url_facebook = self.cleaned_data['url_facebook']
        profile.url_twitter = self.cleaned_data['url_twitter']
        profile.url_linkedin = self.cleaned_data['url_linkedin']
        profile.url_github = self.cleaned_data['url_github']
        profile.url_aboutme = self.cleaned_data['url_aboutme']
        profile.gender = self.cleaned_data['gender']
        profile.howHeard = self.cleaned_data['howHeard']
        profile.industry = self.cleaned_data['industry']
        profile.neighborhood = self.cleaned_data['neighborhood']
        profile.has_kids = self.cleaned_data['has_kids']
        profile.self_emplyed = self.cleaned_data['self_employed']
        profile.company_name = self.cleaned_data['company_name']
        if self.cleaned_data['photo']:
            profile.photo = self.cleaned_data['photo']
        profile.save()
        
        emergency_contact = user.get_emergency_contact()
        emergency_contact.name=self.cleaned_data['emergency_name']
        emergency_contact.relationship=self.cleaned_data['emergency_relationship']
        emergency_contact.phone=self.cleaned_data['emergency_phone']
        emergency_contact.email=self.cleaned_data['emergency_email']
        emergency_contact.save()

class DailyLogForm(forms.Form):
    member_id = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)
    visit_date = forms.DateField(widget=forms.HiddenInput())
    payment = forms.ChoiceField(choices=PAYMENT_CHOICES, required=True)
    #member_list = Member.objects.all()
    #member = forms.ModelChoiceField(queryset=member_list, required=True)
    #guest_of = forms.ModelChoiceField(queryset=member_list, required=False)
    note = forms.CharField(required=False)

    def save(self):
        "Creates the Daily Log to track member activity"
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        # Make sure there isn't another log for this member on this day
        m = Member.objects.get(pk=self.cleaned_data['member_id'])
        v = self.cleaned_data['visit_date']
        daily_log = DailyLog.objects.filter(member=m, visit_date=v)
        if daily_log:
            raise Exception('Member already signed in')

        daily_log = DailyLog()
        daily_log.member = m
        daily_log.visit_date = v
        daily_log.payment = self.cleaned_data['payment']
        #daily_log.guest_of = self.cleaned_data['guest_of']
        daily_log.note = self.cleaned_data['note']
        daily_log.save()
        return daily_log


class MembershipForm(forms.Form):
    member_list = Member.objects.all()
    plan_list = MembershipPlan.objects.filter(enabled=True).order_by('name')
    membership_id = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput)
    member = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)
    membership_plan = forms.ModelChoiceField(queryset=plan_list, required=True)
    start_date = forms.DateField(initial=datetime.date.today)
    end_date = forms.DateField(required=False)
    monthly_rate = forms.IntegerField(required=True, min_value=0)
    dropin_allowance = forms.IntegerField(required=True, min_value=0)
    daily_rate = forms.IntegerField(required=True, min_value=0)
    has_desk = forms.BooleanField(initial=False, required=False)
    has_key = forms.BooleanField(initial=False, required=False)
    has_mail = forms.BooleanField(initial=False, required=False)
    guest_of = forms.ModelChoiceField(queryset=member_list, required=False)
    # These are for the MemberNote
    note = forms.CharField(required=False, widget=forms.Textarea)
    created_by = None

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')
        membership_id = self.cleaned_data['membership_id']

        adding = False
        membership = None
        if membership_id:
            # Editing
            membership = Membership.objects.get(id=membership_id)
        else:
            # Adding
            adding = True
            membership = Membership()

        # Is this right?  Do I really need a DB call so I have the object?
        membership.member = Member.objects.get(id=self.cleaned_data['member'])

        # Any change triggers disabling of the automatic billing
        username = membership.member.user.username
        usaepay.disableAutoBilling(username)
        logger.debug("Automatic Billing Disabled for '%s'" % username)

        # We need to look at their last membership but we'll wait until after the save
        last_membership = membership.member.last_membership()

        # Save this membership
        membership.membership_plan = self.cleaned_data['membership_plan']
        membership.start_date = self.cleaned_data['start_date']
        membership.end_date = self.cleaned_data['end_date']
        membership.monthly_rate = self.cleaned_data['monthly_rate']
        membership.dropin_allowance = self.cleaned_data['dropin_allowance']
        membership.daily_rate = self.cleaned_data['daily_rate']
        membership.has_desk = self.cleaned_data['has_desk']
        membership.has_key = self.cleaned_data['has_key']
        membership.has_mail = self.cleaned_data['has_mail']
        membership.guest_of = self.cleaned_data['guest_of']
        membership.save()

        # Save the note if we were given one
        note = self.cleaned_data['note']
        if note:
            MemberNote.objects.create(member=membership.member, created_by=self.created_by, note=note)

        if adding:
            email.send_new_membership(membership.member.user)

        return membership

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
