from django import forms
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from taggit.forms import *
from members.models import *
from nadine.models.core import Member, HowHeard, Industry, Neighborhood, GENDER_CHOICES, COUNTRY_CHOICES
import datetime
from localflavor.us.us_states import US_STATES
from localflavor.ca.ca_provinces import PROVINCE_CHOICES

def get_state_choices():
    if settings.COUNTRY == 'US':
        return US_STATES
    elif settings.COUNTRY == 'CA':
        return PROVINCE_CHOICES


class EditProfileForm(forms.Form):
    member_id = forms.IntegerField(required=True, min_value=0, widget=forms.HiddenInput)

    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), required=True)
    email2 = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), required=False)
    country = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}),choices=COUNTRY_CHOICES, required=False)
    address1 = forms.CharField(max_length=100, required=False)
    address2 = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=get_state_choices, required=False)
    province = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=PROVINCE_CHOICES, required=True)
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
    has_kids = forms.NullBooleanField(widget=forms.Select(attrs={'class': 'browser-default'}), required=False)
    self_employed = forms.NullBooleanField(widget=forms.Select(attrs={'class': 'browser-default'}), required=False)

    emergency_name = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Name", required=False)
    emergency_relationship = forms.CharField(widget=forms.TextInput(attrs={'size': '50'}), label="Relationship", required=False)
    emergency_phone = forms.CharField(widget=forms.TextInput(attrs={'size': '16'}), label="Phone", required=False)
    emergency_email = forms.EmailField(widget=forms.TextInput(attrs={'size': '50'}), label="E-mail", required=False)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        # Pull the profile to edit
        member_id = self.cleaned_data['member_id']
        profile = Member.objects.get(id=member_id)
        if not member_id or not profile:
            raise Exception('Can not find profile to edit')

        # User data
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        user.save()

        # Profile data
        profile.phone = self.cleaned_data['phone']
        profile.phone2 = self.cleaned_data['phone2']
        profile.email2 = self.cleaned_data['email2']
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
        profile.url_aboutme = self.cleaned_data['url_aboutme']
        profile.url_github = self.cleaned_data['url_github']
        profile.gender = self.cleaned_data['gender']
        profile.howHeard = self.cleaned_data['howHeard']
        profile.industry = self.cleaned_data['industry']
        profile.neighborhood = self.cleaned_data['neighborhood']
        profile.has_kids = self.cleaned_data['has_kids']
        profile.self_emplyed = self.cleaned_data['self_employed']
        profile.company_name = self.cleaned_data['company_name']
        profile.save()

        # Emergency Contact data
        emergency_contact = user.get_emergency_contact()
        emergency_contact.name=self.cleaned_data['emergency_name']
        emergency_contact.relationship=self.cleaned_data['emergency_relationship']
        emergency_contact.phone=self.cleaned_data['emergency_phone']
        emergency_contact.email=self.cleaned_data['emergency_email']
        emergency_contact.save()

        return profile
