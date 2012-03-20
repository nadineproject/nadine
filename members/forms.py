from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from taggit.forms import *
from models import *
from staff.models import *
import datetime
from django.contrib.localflavor.us.us_states import US_STATES

class EditProfileForm(forms.Form):
	member_id = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)
	address1 = forms.CharField(max_length=100, required=False)
	address2 = forms.CharField(max_length=100, required=False)
	city = forms.CharField(max_length=100, required=False)
	state = forms.ChoiceField(choices=US_STATES, required=False)
	zipcode = forms.CharField(max_length=5, required=False)
	phone = forms.CharField(max_length=20, required=False)
	phone2 = forms.CharField(max_length=20, required=False)
	email2 = forms.EmailField(max_length=100, required=False)
	company_name = forms.CharField(max_length=100, required=False)
	url_personal = forms.URLField(required=False)
	url_professional = forms.URLField(required=False)
	url_facebook = forms.URLField(required=False)
	url_twitter = forms.URLField(required=False)
	url_biznik = forms.URLField(required=False)
	url_linkedin = forms.URLField(required=False)
	url_loosecubes = forms.URLField(required=False)
	gender = forms.ChoiceField(choices=GENDER_CHOICES, required=False)
	howHeard = forms.ModelChoiceField(label="How heard", queryset=HowHeard.objects.all(), required=False)
	industry = forms.ModelChoiceField(queryset=Industry.objects.all(), required=False)
	neighborhood = forms.ModelChoiceField(queryset=Neighborhood.objects.all(), required=False)
	has_kids = forms.NullBooleanField(required=False)
	self_employed = forms.NullBooleanField(required=False)

	def save(self):
		if not self.is_valid(): raise Exception('The form must be valid in order to save')
		
		# Pull the profile to edit
		member_id = self.cleaned_data['member_id']
		member = Member.objects.get(id=member_id)
		if not member_id or not member:
			raise Exception('Can not find profile to edit')
			
		# Update all the fields
		member.phone = self.cleaned_data['phone']
		member.phone2 = self.cleaned_data['phone2']
		member.email2 = self.cleaned_data['email2']
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
		member.url_loosecubes = self.cleaned_data['url_loosecubes']
		member.url_biznik = self.cleaned_data['url_biznik']
		member.gender = self.cleaned_data['gender']
		member.howHeard = self.cleaned_data['howHeard']
		member.industry = self.cleaned_data['industry']
		member.neighborhood = self.cleaned_data['neighborhood']
		member.has_kids = self.cleaned_data['has_kids']
		member.self_emplyed = self.cleaned_data['self_employed']
		member.company_name = self.cleaned_data['company_name']
		
		# Fire in the hole!
		member.save()
		return member