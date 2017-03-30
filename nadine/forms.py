import logging
import datetime
import base64
import uuid
import os

from django import forms
from django.core.files.base import ContentFile
from django.forms import modelformset_factory
from django.forms.formsets import BaseFormSet
from django.contrib.auth.models import User
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from django.core.files.base import ContentFile

from localflavor.us.us_states import US_STATES
from localflavor.ca.ca_provinces import PROVINCE_CHOICES

from nadine import email
from nadine.models.core import HowHeard, Industry, Neighborhood, URLType, GENDER_CHOICES
from nadine.models.profile import UserProfile, MemberNote, user_photo_path
from nadine.models.membership import Membership, MembershipPlan, MembershipPackage, ResourceSubscription, IndividualMembership
from nadine.models.usage import PAYMENT_CHOICES, CoworkingDay
from nadine.models.resource import Room, Resource
from nadine.models.organization import Organization, OrganizationMember
from nadine.utils.payment_api import PaymentAPI
from member.models import HelpText, MOTD

logger = logging.getLogger(__name__)


class DateRangeForm(forms.Form):
    start = forms.DateField()
    end = forms.DateField()


class OrganizationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            self.instance = kwargs['instance']
            del kwargs['instance']
        super(OrganizationForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'instance'):
            self.initial['org_id'] = self.instance.id
            self.initial['name'] = self.instance.name
            self.initial['blurb'] = self.instance.blurb
            self.initial['bio'] = self.instance.bio
            self.initial['photo'] = self.instance.photo
            self.initial['public'] = self.instance.public
            #self.initial['locked'] = self.instance.locked

    org_id = forms.IntegerField(required=True, widget=forms.HiddenInput)
    name = forms.CharField(max_length=128, label="Organization Name", required=True, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    blurb = forms.CharField(widget=forms.Textarea, max_length=112, required=False)
    bio = forms.CharField(widget=forms.Textarea, max_length=512, required=False)
    photo = forms.FileField(required=False)
    public = forms.BooleanField(required=False)
    #locked = forms.BooleanField(required=False)

    def save(self):
        org_id = self.cleaned_data['org_id']
        org = Organization.objects.get(id=org_id)
        org.name = self.cleaned_data['name']
        org.blurb = self.cleaned_data['blurb']
        org.bio = self.cleaned_data['bio']
        if self.cleaned_data['photo']:
            # Delete the old one before we save the new one
            org.photo.delete()
            org.photo = self.cleaned_data['photo']
        if 'public' in self.cleaned_data:
            org.public = self.cleaned_data['public']
        if 'locked' in self.cleaned_data:
            org.locked = self.cleaned_data['locked']
        org.save()


class OrganizationSearchForm(forms.Form):
    terms = forms.CharField(max_length=100)


class OrganizationMemberForm(forms.Form):
    def __init__(self, *args, **kwargs):
        if 'instance' in kwargs:
            self.instance = kwargs['instance']
            del kwargs['instance']
        super(OrganizationMemberForm, self).__init__(*args, **kwargs)
        if hasattr(self, 'instance'):
            self.initial['member_id'] = self.instance.id
            self.initial['org_id'] = self.instance.organization.id
            self.initial['username'] = self.instance.user.username
            self.initial['title'] = self.instance.title
            self.initial['start_date'] = self.instance.start_date
            self.initial['end_date'] = self.instance.end_date
            self.initial['admin'] = self.instance.admin

    org_id = forms.IntegerField(required=True, widget=forms.HiddenInput)
    member_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    username = forms.CharField(required=False, widget=forms.HiddenInput)
    title = forms.CharField(max_length=128, required=False, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    start_date = forms.DateField(widget=forms.DateInput(attrs={'placeholder':'e.g. 12/28/16', 'class':'datepicker'}, format='%m/%d/%Y'), required=True)
    end_date = forms.DateField(widget=forms.DateInput(attrs={'placeholder':'e.g. 12/28/16', 'class':'datepicker'}, format='%m/%d/%Y'), required=False)
    admin = forms.BooleanField(required=False)

    def is_valid(self):
        # run the parent validation first
        super_valid = super(OrganizationMemberForm, self).is_valid()
        has_member_id = 'member_id' in self.cleaned_data and self.cleaned_data['member_id']
        has_username = 'username' in self.cleaned_data and self.cleaned_data['username']
        if not (has_member_id or has_username):
            self.add_error('username', 'No user data provided')
        return super_valid and (has_member_id or has_username)

    def clean_member(self):
        self.member = None
        self.organization = Organization.objects.get(id=self.cleaned_data['org_id'])

        # Populate our member from either member_id (edit) or username (add)
        member_id = self.cleaned_data['member_id']
        username=self.cleaned_data['username']
        if member_id:
            self.member = OrganizationMember.objects.get(id=member_id)
        elif username:
            user = User.objects.get(username=username)
            self.member = OrganizationMember(organization=self.organization, user=user)
        else:
            raise Exception("Form must contain member_id or username!")

        return self.member

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')
        member = self.clean_member()
        member.title = self.cleaned_data['title']
        member.start_date = self.cleaned_data['start_date']
        member.end_date = self.cleaned_data['end_date']
        if 'admin' in self.cleaned_data:
            member.admin = self.cleaned_data['admin']
        member.save()


class PayBillsForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.HiddenInput)
    amount = forms.DecimalField(min_value=0, max_value=10000, required=True, max_digits=7, decimal_places=2)
    transaction_note = forms.CharField(required=False, widget=forms.Textarea)


class MemberSearchForm(forms.Form):
    terms = forms.CharField(max_length=100)


class NewUserForm(forms.Form):
    first_name = forms.CharField(max_length=100, label="First name *", required=True, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    last_name = forms.CharField(max_length=100, label="Last name *", required=True, widget=forms.TextInput(attrs={'autocapitalize': "words"}))
    email = forms.EmailField(max_length=100, label="Email *", required=True)

    def clean_first_name(self):
        return self.cleaned_data['first_name'].strip().title()

    def clean_last_name(self):
        return self.cleaned_data['last_name'].strip().title()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).count() > 0:
            raise forms.ValidationError("Email address '%s' already in use." % email)
        return email

    def create_username(self, suffix=""):
        clean_first = self.cleaned_data['first_name'].strip().lower()
        clean_last = self.cleaned_data['last_name'].strip().lower()
        username = "%s_%s%s" % (clean_first, clean_last, suffix)
        clean_username = username.replace(" ", "_")
        clean_username = clean_username.replace(".", "_")
        clean_username = clean_username.replace("-", "_")
        clean_username = clean_username.replace("+", "")
        clean_username = clean_username.replace("@", "")
        clean_username = clean_username.replace("'", "")
        return clean_username

    def save(self):
        "Creates the User and Profile records with the field data and returns the user"
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        # Generate a unique username
        tries = 1
        username = self.create_username()
        while User.objects.filter(username=username).count() > 0:
            tries = tries + 1
            username = self.create_username(suffix=tries)

        first = self.cleaned_data['first_name']
        last = self.cleaned_data['last_name']
        email = self.cleaned_data['email']

        user = User(username=username, first_name=first, last_name=last, email=email)
        password = User.objects.make_random_password(length=32)
        user.set_password(password)
        user.save()

        return user

    class Meta:
        widgets = {
            'first_name': forms.TextInput(attrs={'autocapitalize': 'on', 'autocorrect': 'off'}),
            'last_name': forms.TextInput(attrs={'autocapitalize': 'on', 'autocorrect': 'off'}),
        }


def get_state_choices():
    if settings.COUNTRY == 'US':
        return US_STATES
    elif settings.COUNTRY == 'CA':
        return PROVINCE_CHOICES


class ProfileImageForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.HiddenInput)
    photo = forms.FileField(required=False)
    cropped_image_data = forms.CharField(widget=forms.HiddenInput())

    def save(self):
        user = User.objects.get(username=self.cleaned_data['username'])
        filename = "user_photos/%s.png" % self.cleaned_data['username']
        raw_img_data = self.cleaned_data['cropped_image_data']
        if not raw_img_data or len(raw_img_data) == 0:
            # Nothing to save here
            return
        img_data = base64.b64decode(raw_img_data)
        if user.profile.photo:
            user.profile.photo.delete()
        user.profile.photo.save(filename, ContentFile(img_data))


class BaseLinkFormSet(BaseFormSet):
    def clean(self):
        if any(self.errors):
            return

        url_types = []
        urls = []

        for form in self.forms:
            if form.cleaned_data:
                username = form.cleaned_data['username']
                org_id = form.cleaned_data['org_id']
                url_type = form.cleaned_data['url_type']
                url = form.cleaned_data['url']
                if url_type and url :
                    urls.append(url)
                if url and not url_type:
                    raise forms.ValidationError(message='All websites must have a URL', code='missing_anchor')
                if url_type and not url:
                    raise forms.ValidationError(message='All URLS must have a type', code='missing_type')


class LinkForm(forms.Form):
    username = forms.CharField(required=False, widget=forms.HiddenInput)
    org_id = forms.IntegerField(required=False, widget=forms.HiddenInput)
    url_type = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), label='Website Type', queryset=URLType.objects.all(), required=False)
    url = forms.URLField(widget=forms.URLInput(attrs={'placeholder': 'http://www.facebook.com/myprofile'}), required=False)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        if self.cleaned_data['username']:
            user = User.objects.get(username=self.cleaned_data['username'])
            user.profile.save_url(self.cleaned_data['url_type'], self.cleaned_data['url'])
        if self.cleaned_data['org_id']:
            org = Organization.objects.get(id=self.cleaned_data['org_id'])
            org.save_url(self.cleaned_data['url_type'], self.cleaned_data['url'])


class EditProfileForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.HiddenInput)
    first_name = forms.CharField(max_length=100, required=True)
    last_name = forms.CharField(max_length=100, required=True)
    address1 = forms.CharField(max_length=100, required=False)
    address2 = forms.CharField(max_length=100, required=False)
    city = forms.CharField(max_length=100, required=False)
    state = forms.ChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), choices=get_state_choices, required=False)
    zipcode = forms.CharField(max_length=16, required=False)
    phone = forms.CharField(max_length=20, required=False)
    phone2 = forms.CharField(max_length=20, required=False)
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
    public_profile = forms.BooleanField(required=False)

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
        user.profile.self_employed = self.cleaned_data['self_employed']
        user.profile.public_profile = self.cleaned_data['public_profile']
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


class CoworkingDayForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={'readonly':'readonly'}))
    visit_date = forms.DateField(widget=forms.HiddenInput())
    payment = forms.ChoiceField(choices=PAYMENT_CHOICES, required=True)
    note = forms.CharField(required=False)

    def save(self):
        "Creates the Daily Log to track member activity"
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        # Make sure there isn't another log for this member on this day
        u = User.objects.get(username=self.cleaned_data['username'])
        v = self.cleaned_data['visit_date']
        if CoworkingDay.objects.filter(user=u, visit_date=v).count() > 0:
            raise Exception('Member already signed in')

        day = CoworkingDay()
        day.user = u
        day.visit_date = v
        day.payment = self.cleaned_data['payment']
        day.note = self.cleaned_data['note']
        day.save()
        return day


class MembershipForm(forms.Form):
    username = forms.CharField(required=True, widget=forms.HiddenInput)
    plan_list = MembershipPlan.objects.filter(enabled=True).order_by('name')
    membership_id = forms.IntegerField(required=False, min_value=0, widget=forms.HiddenInput)
    membership_plan = forms.ModelChoiceField(queryset=plan_list, required=True)
    start_date = forms.DateField(initial=datetime.date.today)
    end_date = forms.DateField(required=False)
    monthly_rate = forms.IntegerField(required=True, min_value=0)
    dropin_allowance = forms.IntegerField(required=True, min_value=0)
    daily_rate = forms.IntegerField(required=True, min_value=0)
    has_desk = forms.BooleanField(initial=False, required=False)
    has_key = forms.BooleanField(initial=False, required=False)
    has_mail = forms.BooleanField(initial=False, required=False)
    paid_by = forms.ModelChoiceField(queryset=User.helper.active_members(), required=False)
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

        username = self.cleaned_data['username']
        membership.user = User.objects.get(username=username)
        membership.member = membership.user.profile

        # Any change triggers disabling of the automatic billing
        try:
            api = PaymentAPI()
            api.disable_recurring(username)
            logger.debug("Automatic Billing Disabled for '%s'" % username)
        except Exception as e:
            logger.error(e)

        # We need to look at their last membership but we'll wait until after the save
        last_membership = membership.user.profile.last_membership()

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
        membership.paid_by = self.cleaned_data['paid_by']
        membership.save()

        # Save the note if we were given one
        note = self.cleaned_data['note']
        if note:
            MemberNote.objects.create(user=membership.user, created_by=self.created_by, note=note)

        if adding:
            email.send_new_membership(membership.user)

        return membership

class SubForm(forms.Form):
    username = forms.CharField(required=False, widget=forms.HiddenInput({'class':'username_td'}))
    created_ts = forms.DateField(required=False, widget=forms.HiddenInput)
    created_by = forms.CharField(required=False, widget=forms.HiddenInput({'class':'created_by_td'}))
    s_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    resource = forms.ModelChoiceField(queryset=Resource.objects.all(), required=False)
    allowance = forms.IntegerField(required=False)
    start_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'start_date'}), required=False)
    end_date = forms.DateField(widget=forms.TextInput(attrs={'class': 'end_date'}), required=False)
    monthly_rate = forms.IntegerField(required=False)
    overage_rate = forms.IntegerField(required=False)
    paid_by = forms.CharField(widget=forms.TextInput(attrs={'class': 'paying_user'}), max_length=128, required=False)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')

        username = self.cleaned_data['username']
        user = User.objects.get(username=username)
        if self.cleaned_data['created_ts']:
            created_ts = self.cleaned_data['created_ts']
        else:
            created_ts = timezone.now()
        if self.cleaned_data['s_id']:
            s_id = self.cleaned_data['id']

        created_by_user = self.cleaned_data['created_by']
        created_by = User.objects.get(username=created_by_user)
        resource = self.cleaned_data['resource']
        allowance = self.cleaned_data['allowance']
        start_date = self.cleaned_data['start_date']
        end_date = self.cleaned_data['end_date']
        monthly_rate = self.cleaned_data['monthly_rate']
        overage_rate = self.cleaned_data['overage_rate']
        if self.cleaned_data['paid_by']:
            paid_by = self.cleaned_data['paid_by']
        else:
            paid_by = None

        if s_id:
            sub = ResourceSubscription.objects.get(id=s_id)
            sub.end_date = end_date
        else:
            sub = ResourceSubscription(created_ts=created_ts, created_by=created_by, resource=resource, allowance=allowance, start_date=start_date, end_date=end_date, monthly_rate=monthly_rate, overage_rate=overage_rate, paid_by=paid_by, membership=user.membership)

        sub.save()

        return sub

class MembershipPackageForm(forms.Form):
    username = forms.CharField(required=False, widget=forms.HiddenInput)
    org = forms.CharField(required=False, widget=forms.HiddenInput)
    package = forms.ModelChoiceField(widget=forms.Select(attrs={'class': 'browser-default'}), label='Choose a Package', queryset=MembershipPackage.objects.all(), required=True)
    bill_day = forms.IntegerField(min_value=1, max_value=31, required=True)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')
        package = self.cleaned_data['package']
        bill_day = self.cleaned_data['bill_day']
        if self.cleaned_data['username'] and self.cleaned_data['org']:
            raise Exception('You cannot save a membership for an organization AND a user in the same form.')
        elif self.cleaned_data['username']:
            username = self.cleaned_data['username']
            to_update = User.objects.get(username=username)
        elif self.cleaned_data['org']:
            org = self.cleaned_data['username']
            to_update = Organization.objects.get(id=org)
        else:
            raise Exception('A user or organization is required to save a membership.')
        membership = to_update.membership
        membership.package = package
        membership.bill_day = bill_day
        membership.save()

        return membership


class HelpTextForm(forms.Form):
    title = forms.CharField(max_length=128, label='Help Text Title', required=True, widget=forms.TextInput(attrs={'autocapitalize': "words", "placeholder":"e.g. Welcome Info"}))
    template = forms.CharField(widget=forms.Textarea(attrs={'placeholder':'<h1>Hello World</h1>'}), required=True)
    slug = forms.CharField(widget=forms.TextInput(attrs={"placeholder":"Single Word for URL e.g. 'hello'"}), max_length=16, required=True)
    order = forms.IntegerField(required=True, widget=forms.HiddenInput)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')
        title = self.cleaned_data['title']
        template = self.cleaned_data['template']
        slug = self.cleaned_data['slug']
        order = self.cleaned_data['order']

        help_text = HelpText(title=title, template=template, slug=slug, order=order)
        help_text.save()

        return help_text

class MOTDForm(forms.Form):
    start_ts = forms.DateField(initial=datetime.date.today, required=True)
    end_ts = forms.DateField(required=False)
    message = forms.CharField(required=True)
    delay_ms = forms.IntegerField(required=True, widget=forms.HiddenInput)

    def save(self):
        if not self.is_valid():
            raise Exception('The form must be valid in order to save')
        start_ts = self.cleaned_data['start_ts']
        end_ts = self.cleaned_data['end_ts']
        message = self.cleaned_data['message']
        delay_ms = self.cleaned_data['delay_ms']

        motd = MOTD(start_ts=start_ts, end_ts=end_ts, message=message, delay_ms=delay_ms)
        motd.save()

        return motd


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
