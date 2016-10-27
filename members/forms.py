import datetime

from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags

from taggit.forms import *
from members.models import *
from nadine.models.core import UserProfile, HowHeard, Industry, Neighborhood, GENDER_CHOICES
from localflavor.us.us_states import US_STATES
from localflavor.ca.ca_provinces import PROVINCE_CHOICES

from nadine.models.resource import Room

def get_state_choices():
    if settings.COUNTRY == 'US':
        return US_STATES
    elif settings.COUNTRY == 'CA':
        return PROVINCE_CHOICES


class EditProfileForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.HiddenInput)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    address1 = forms.CharField(max_length=100, required=False)
    address2 = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=get_state_choices, required=False)
    zipcode = forms.CharField(max_length=16, required=False)
    photo = forms.FileField(required=False)
    phone = forms.CharField(max_length=20, required=False)
    phone2 = forms.CharField(max_length=20, required=False)
    company_name = forms.CharField(max_length=100, required=False)
    url_personal = forms.URLField(required=False)
    url_professional = forms.URLField(required=False)
    url_facebook = forms.URLField(required=False)
    url_twitter = forms.URLField(required=False)
    url_linkedin = forms.URLField(required=False)
    url_github = forms.URLField(required=False)
    gender = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=GENDER_CHOICES, required=False)
    howHeard = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), label="How heard", queryset=HowHeard.objects.all(), required=False)
    industry = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), queryset=Industry.objects.all(), required=False)
    neighborhood = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), queryset=Neighborhood.objects.all(), required=False)
    bio = forms.CharField(widget=forms.Textarea, max_length=512, required=False)
    has_kids = forms.NullBooleanField(widget=forms.NullBooleanSelect(attrs={'class':'browser-default'}), required=False)
    self_employed = forms.NullBooleanField(widget=forms.NullBooleanSelect(attrs={'class':'browser-default'}), required=False)
    public_profile = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=((True, 'Yes'), (False, 'No')), required=True)

    emergency_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Name", required=False)
    emergency_relationship = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Relationship", required=False)
    emergency_phone = forms.CharField(widget=forms.TextInput(attrs={'size': '16'}), label="Phone", required=False)
    emergency_email = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), label="E-mail", required=False)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        user = User.objects.get(username=self.cleaned_data['username'])
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Profile data
        user.profile.phone = self.cleaned_data['phone']
        user.profile.phone2 = self.cleaned_data['phone2']
        user.profile.address1 = self.cleaned_data['address1']
        user.profile.address2 = self.cleaned_data['address2']
        user.profile.city = self.cleaned_data['city']
        user.profile.state = self.cleaned_data['state']
        user.profile.zipcode = self.cleaned_data['zipcode']
        user.profile.bio = self.cleaned_data['bio']
        user.profile.gender = self.cleaned_data['gender']
        user.profile.howHeard = self.cleaned_data['howHeard']
        user.profile.industry = self.cleaned_data['industry']
        user.profile.neighborhood = self.cleaned_data['neighborhood']
        user.profile.has_kids = self.cleaned_data['has_kids']
        user.profile.self_emplyed = self.cleaned_data['self_employed']
        user.profile.company_name = self.cleaned_data['company_name']
        user.profile.public_profile = self.cleaned_data['public_profile']
        if self.cleaned_data['photo']:
            user.profile.photo = self.cleaned_data['photo']
        user.profile.save()

        # Save the URLs
        user.profile.save_url("personal", self.cleaned_data['url_personal'])
        user.profile.save_url("professional", self.cleaned_data['url_professional'])
        user.profile.save_url("facebook", self.cleaned_data['url_facebook'])
        user.profile.save_url("twitter", self.cleaned_data['url_twitter'])
        user.profile.save_url("linkedin", self.cleaned_data['url_linkedin'])
        user.profile.save_url("github", self.cleaned_data['url_github'])

        # Emergency Contact data
        emergency_contact = user.get_emergency_contact()
        emergency_contact.name=self.cleaned_data['emergency_name']
        emergency_contact.relationship=self.cleaned_data['emergency_relationship']
        emergency_contact.phone=self.cleaned_data['emergency_phone']
        emergency_contact.email=self.cleaned_data['emergency_email']
        emergency_contact.save()

        return user.profile


class EventForm(forms.Form):
    user = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), queryset=User.objects.order_by('first_name'))
    room = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), queryset=Room.objects.all(), required=False)
    start_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'placeholder':'e.g. 12/28/16 14:30'}, format='%m/%d/%Y %H:%M'), required=True)
    end_time = forms.DateTimeField(widget=forms.DateTimeInput(attrs={'placeholder':'e.g. 12/28/16 16:30'}, format='%m/%d/%Y %H:%M:%S'), required=True)
    description = forms.CharField(max_length=100, required=False)
    charge = forms.DecimalField(decimal_places=2, max_digits=9, required=True)
    publicly_viewable = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=((True, 'Yes'), (False, 'No')), required=False)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        user = self.cleaned_data['user']
        room = self.cleaned_data['room']
        start_ts = self.cleaned_data['start_time']
        end_ts = self.cleaned_data['end_time']
        description = self.cleaned_data['description']
        charge = self.cleaned_data['charge']
        is_public = self.cleaned_data['publicly_viewable']

        event = Event(user=user, room=room, start_ts=start_ts, end_ts=end_ts, description=description, charge=charge, is_public=is_public)

        event.save()

        return event
