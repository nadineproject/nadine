from django import forms
from django.contrib.auth.models import User

from interlink.models import MailingList

class MailingListSubscriptionForm(forms.Form):
	subscribe = forms.CharField(required=False, widget=forms.HiddenInput)
	mailing_list_id = forms.IntegerField(required=True, widget=forms.HiddenInput)

	def save(self, user):
		list = MailingList.objects.get(pk=self.cleaned_data['mailing_list_id'])
		if self.cleaned_data['subscribe'] == 'true':
			list.subscribers.add(user)
		elif self.cleaned_data['subscribe'] == 'false' and user in list.subscribers.all():
			list.subscribers.remove(user)

# Copyright 2011 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
