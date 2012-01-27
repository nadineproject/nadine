from django.contrib.sites.models import Site

from staff.models import Onboard_Task, Bill, ExitTask
from staff.forms import MemberSearchForm
from members.models import HelpText

def site(request):
	"""Adds a site context variable"""
	return {'site': Site.objects.get_current() }

def nav_context(request):
	"""Adds variables used by the nav bar"""

	billing_count = Bill.objects.filter(transactions__isnull=True).count()
	site_search_form = MemberSearchForm()
	return {'billing_count':billing_count, 'site_search_form':site_search_form }

# Copyright 2010 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
