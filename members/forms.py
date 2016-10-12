import datetime

from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags

from taggit.forms import *
from members.models import *
from nadine.models.core import UserProfile, HowHeard, Industry, Neighborhood, GENDER_CHOICES
from localflavor.us.us_states import US_STATES
from localflavor.ca.ca_provinces import PROVINCE_CHOICES


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
    url_aboutme = forms.URLField(required=False)
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
        user.profile.url_personal = self.cleaned_data['url_personal']
        user.profile.url_professional = self.cleaned_data['url_professional']
        user.profile.url_facebook = self.cleaned_data['url_facebook']
        user.profile.url_twitter = self.cleaned_data['url_twitter']
        user.profile.url_linkedin = self.cleaned_data['url_linkedin']
        user.profile.url_aboutme = self.cleaned_data['url_aboutme']
        user.profile.url_github = self.cleaned_data['url_github']
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

        # Emergency Contact data
        emergency_contact = user.get_emergency_contact()
        emergency_contact.name=self.cleaned_data['emergency_name']
        emergency_contact.relationship=self.cleaned_data['emergency_relationship']
        emergency_contact.phone=self.cleaned_data['emergency_phone']
        emergency_contact.email=self.cleaned_data['emergency_email']
        emergency_contact.save()

        return user.profile
