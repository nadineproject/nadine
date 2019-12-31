from django import forms
from django.contrib.sites.models import Site

from interlink.models import MailingList, OutgoingMail


class MailingListSubscriptionForm(forms.Form):
    subscribe = forms.CharField(required=False, widget=forms.HiddenInput)
    mailing_list_id = forms.IntegerField(required=True, widget=forms.HiddenInput)

    def save(self, user):
        mailing_list = MailingList.objects.get(pk=self.cleaned_data['mailing_list_id'])
        if mailing_list.moderator_controlled:
            return False

        body = 'So says https://%s ' % Site.objects.get_current().domain
        if self.cleaned_data['subscribe'] == 'true' and (user.profile.is_active() or user.is_staff):
            mailing_list.subscribe(user)
            subject = '%s subscribed to %s' % (user.get_full_name(), mailing_list.name)
            OutgoingMail.objects.create(mailing_list=mailing_list, subject=subject, body=body, moderators_only=True)
        elif self.cleaned_data['subscribe'] == 'false' and user in mailing_list.subscribers.all():
            mailing_list.unsubscribe(user)
            subject = '%s unsubscribed from %s' % (user.get_full_name(), mailing_list.name)
            OutgoingMail.objects.create(mailing_list=mailing_list, subject=subject, body=body, moderators_only=True)
        return True

# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
