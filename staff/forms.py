from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.utils import timezone
from taggit.forms import *

from staff.models import *
from staff import email
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
	
class NewUserForm(forms.Form):
	first_name = forms.CharField(max_length=100, label="First name *", required=True)
	last_name = forms.CharField(max_length=100, label="Last name *", required=True)
	email = forms.EmailField(max_length=100, label="Email *", required=True)
	#phone = forms.CharField(max_length=100, required=False)

	def save(self):
		"Creates the User and Member records with the field data and returns the user"
		if not self.is_valid(): raise Exception('The form must be valid in order to save')
		
		first = self.cleaned_data['first_name'].strip().title()
		if len(first) == 0: raise forms.ValidationError("First Name Required.")
		last = self.cleaned_data['last_name'].strip().title()
		if len(last) == 0: raise forms.ValidationError("Last Name Required.")
		email = self.cleaned_data['email'].strip().lower()
		if len(email) == 0: raise forms.ValidationError("Email Required.")
		if User.objects.filter(email=email).count() > 0: raise forms.ValidationError("Email address '%s' already in use." % email)
		username = "%s_%s" % (first.lower(), last.lower())
		if User.objects.filter(username=username).count() > 0: raise forms.ValidationError("Username '%s' already in use." % username)

		user = User(username=username, first_name=first, last_name=last, email=email)
		user.save()
		#member = user.get_profile()
		#member.phone = self.cleaned_data['phone'].strip()
		#member.save()
		
		return user

class MemberSearchForm(forms.Form):
	terms = forms.CharField(max_length=100)

class MemberSignupForm(forms.Form):
	username = forms.RegexField(max_length=30, regex=r'^[\w.@+-]+$', help_text = "Required. 30 characters or fewer. Letters, digits and @/./+/-/_ only.", error_messages = {'invalid': "This value may contain only letters, numbers and @/./+/-/_ characters."}, label="Username *")
	first_name = forms.CharField(max_length=100, label="First name *")
	last_name = forms.CharField(max_length=100, label="Last name *")
	email = forms.EmailField(max_length=100, label="Email *")
	email2 = forms.EmailField(max_length=100, required=False)
	phone = forms.CharField(max_length=100, required=False)
	phone2 = forms.CharField(max_length=100, required=False)
	address1 = forms.CharField(max_length=100, required=False)
	address2 = forms.CharField(max_length=100, required=False)
	city = forms.CharField(max_length=100, required=False)
	state = forms.CharField(max_length=100, required=False)
	zipcode = forms.CharField(max_length=100, required=False)
	company_name = forms.CharField(max_length=100, required=False)
	url_personal = forms.URLField(required=False)
	url_professional = forms.URLField(required=False)
	url_facebook = forms.URLField(required=False)
	url_twitter = forms.URLField(required=False)
	url_biznik = forms.URLField(required=False)
	url_linkedin = forms.URLField(required=False)
	url_github = forms.URLField(required=False)
	url_aboutme = forms.URLField(required=False)
	gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
	howHeard = forms.ModelChoiceField(label="How heard", queryset=HowHeard.objects.all(), required=False)
	industry = forms.ModelChoiceField(queryset=Industry.objects.all(), required=False)
	neighborhood = forms.ModelChoiceField(queryset=Neighborhood.objects.all(), required=False)
	has_kids = forms.NullBooleanField(required=False)
	self_employed = forms.NullBooleanField(required=False)
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
		member.email2 = self.cleaned_data['email2']
		member.phone = self.cleaned_data['phone']
		member.phone = self.cleaned_data['phone2']
		member.address1 = self.cleaned_data['address1']
		member.address2 = self.cleaned_data['address2']
		member.city = self.cleaned_data['city']
		member.state = self.cleaned_data['state']
		member.zipcode = self.cleaned_data['zipcode']
		member.url_personal = self.cleaned_data['url_personal']
		member.url_professional = self.cleaned_data['url_professional']
		member.url_facebook = self.cleaned_data['url_facebook']
		member.url_twitter = self.cleaned_data['url_twitter']
		member.url_linkedin = self.cleaned_data['url_linkedin']
		member.url_biznik = self.cleaned_data['url_biznik']
		member.url_github = self.cleaned_data['url_github']
		member.url_aboutme = self.cleaned_data['url_aboutme']
		member.gender = self.cleaned_data['gender']
		member.howHeard = self.cleaned_data['howHeard']
		member.industry = self.cleaned_data['industry']
		member.neighborhood = self.cleaned_data['neighborhood']
		member.has_kids = self.cleaned_data['has_kids']
		member.self_emplyed = self.cleaned_data['self_employed']
		member.company_name = self.cleaned_data['company_name']
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

class MembershipForm(forms.Form):
	member_list = Member.objects.all();
	plan_list = MembershipPlan.objects.all();
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
		if not self.is_valid(): raise Exception('The form must be valid in order to save')
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
		
		# If this is a new membership and they have an old membership that is at least 5 days old
		# Then remove all the onboarding tasks and the exit tasks so they have a clean slate
		if adding and last_membership and last_membership.end_date:
			if last_membership.end_date < timezone.now().date() - timedelta(5):
				for completed_task in Onboard_Task_Completed.objects.filter(member=membership.member):
					completed_task.delete()
				for completed_task in ExitTaskCompleted.objects.filter(member=membership.member):
					completed_task.delete()

		if adding:
			email.send_new_membership(membership.member.user)

		return membership

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
