from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags

from models import *

import datetime

class DateRangeForm(forms.Form):
   start = forms.DateField()
   end = forms.DateField()

class PayBillsForm(forms.Form):
   member_id = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)
   amount = forms.DecimalField(min_value=0, max_value=10000, required=True, max_digits=7, decimal_places=2)
   transaction_note = forms.CharField(required=False, widget=forms.Textarea)

class RunBillingForm(forms.Form):
   run_billing = forms.BooleanField(required=True, widget=forms.HiddenInput)
   
class MemberSearchForm(forms.Form):
   terms = forms.CharField(max_length=100)

class MemberSignupForm(forms.Form):
   username = forms.RegexField(max_length=30, regex=r'^[\w.@+-]+$', help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.", error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."}, label="Username *")
   first_name = forms.CharField(max_length=100, label="First name *")
   last_name = forms.CharField(max_length=100, label="Last name *")
   email = forms.EmailField(max_length=100, required=False)
   phone = forms.CharField(max_length=100, required=False)
   website = forms.URLField(required=False)
   gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
   howHeard = forms.ModelChoiceField(label="How heard", queryset=HowHeard.objects.all(), required=False)
   industry = forms.ModelChoiceField(queryset=Industry.objects.all(), required=False)
   neighborhood = forms.ModelChoiceField(queryset=Neighborhood.objects.all(), required=False)
   has_kids = forms.NullBooleanField(required=False)
   self_employed = forms.NullBooleanField(required=False)
   company_name = forms.CharField(max_length=100, required=False)
   notes = forms.CharField(required=False)
   photo = forms.ImageField(required=False)

   def clean_username(self):
      data = self.cleaned_data['username']
      if User.objects.filter(username=data).count() > 0: raise forms.ValidationError("That username is already in use.")
      return data
   
   def save(self):
      "Creates the User and Member records with the field data and returns the user"
      if not self.is_valid(): raise Exception('The form must be valid in order to save')
      user = User(username=self.cleaned_data['username'], first_name=self.cleaned_data['first_name'], last_name=self.cleaned_data['last_name'], email=self.cleaned_data['email'])
      user.save()
      member = user.get_profile()
      member.phone = self.cleaned_data['phone']
      member.website = self.cleaned_data['website']
      member.gender = self.cleaned_data['gender']
      member.howHeard = self.cleaned_data['howHeard']
      member.industry = self.cleaned_data['industry']
      member.neighborhood = self.cleaned_data['neighborhood']
      member.has_kids = self.cleaned_data['has_kids']
      member.self_emplyed = self.cleaned_data['self_employed']
      member.company_name = self.cleaned_data['company_name']
      member.notes = self.cleaned_data['notes']
      member.photo = self.cleaned_data['photo']
      member.save()
      return user

class DailyLogForm(forms.Form):
   member_list = Member.objects.all();
   visit_date = forms.DateField(widget=forms.HiddenInput())
   member = forms.ModelChoiceField(queryset=member_list, required=True)
   payment = forms.ChoiceField(choices=PAYMENT_CHOICES, required=True)
   guest_of = forms.ModelChoiceField(queryset=member_list, required=False)
   notes = forms.CharField(required=False)

   def save(self):
      "Creates the Daily Log to track member activity"
      if not self.is_valid(): raise Exception('The form must be valid in order to save')
      daily_log = DailyLog()
      daily_log.member = self.cleaned_data['member']
      daily_log.visit_date = self.cleaned_data['visit_date']
      daily_log.payment = self.cleaned_data['payment']
      daily_log.guest_of = self.cleaned_data['guest_of']
      daily_log.notes = self.cleaned_data['notes']
      daily_log.save()
      return daily_log

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
