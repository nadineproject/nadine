from django.conf import settings
from nadine.forms import MemberSearchForm


def nav_context(request):
    site_search_form = MemberSearchForm()
    return {'site_search_form': site_search_form}


def tablet_context(request):
    try:
        return {'tablet_ios': settings.TABLET.lower() == 'ios'}
    except AttributeError:
        return {'tablet_ios': False}


def allow_online_registration(request):
    return {'ALLOW_ONLINE_REGISTRATION': settings.ALLOW_ONLINE_REGISTRATION}


# Copyright 2021 Office Nomads LLC (https://officenomads.com/) Licensed under the AGPL License, Version 3.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://www.gnu.org/licenses/agpl-3.0.html. Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

