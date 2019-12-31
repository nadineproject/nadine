import base64
import hmac
import hashlib
import urllib.request, urllib.parse, urllib.error

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, HttpResponseRedirect
from django.urls import reverse

from django.conf import settings

from urllib.parse import parse_qs

@login_required
def sso(request):
    payload = request.GET.get('sso')
    signature = request.GET.get('sig')

    if None in [payload, signature]:
        return HttpResponseBadRequest('No SSO payload or signature. Please contact support if this problem persists.')

    ## Validate the payload

    try:
        payload = urllib.parse.unquote(payload)
        decoded = base64.decodestring(payload)
        assert 'nonce' in decoded
        assert len(payload) > 0
    except AssertionError:
        return HttpResponseBadRequest('Invalid payload. Please contact support if this problem persists.')

    key = str(settings.DISCOURSE_SSO_SECRET) # must not be unicode
    h = hmac.new(key, payload, digestmod=hashlib.sha256)
    this_signature = h.hexdigest()

    if this_signature != signature:
        return HttpResponseBadRequest('Invalid payload. Please contact support if this problem persists.')

    ## Build the return payload

    qs = parse_qs(decoded)
    params = {
        'nonce': qs['nonce'][0],
        'email': request.user.email,
        'external_id': request.user.id,
        'username': request.user.username,
        'name': request.user.get_full_name(),
        'avatar_url': request.build_absolute_uri(request.user.profile.photo.url),
        'avatar_force_update': True,
        'admin': request.user.is_staff,
        'moderator': request.user.is_staff
    }

    return_payload = base64.encodestring(urllib.parse.urlencode(params))
    h = hmac.new(key, return_payload, digestmod=hashlib.sha256)
    query_string = urllib.parse.urlencode({'sso': return_payload, 'sig': h.hexdigest()})

    ## Redirect back to Discourse

    url = '%s/session/sso_login' % settings.DISCOURSE_BASE_URL
    return HttpResponseRedirect('%s?%s' % (url, query_string))


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
