

import json
import requests
import datetime
import logging
import email.utils
from collections import OrderedDict

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from django.template import Template, TemplateDoesNotExist
from django.template.loader import get_template
from django.utils import timezone


logger = logging.getLogger(__name__)


class MailgunException(Exception):
    pass


def address_map(mailgun_data, key, exclude=None):
    if not exclude: exclude = []
    a_map = OrderedDict()
    if key in mailgun_data:
        for a in mailgun_data[key]:
            name, address = email.utils.parseaddr(a)
            if not address in exclude:
                a_map[address.lower()] = a
        # print("mailgun_data[%s] = %s" % (key, mailgun_data[key]))
        # print("exclude = %s" % exclude)
        # print("a_map = %s" % a_map)
    return a_map


def clean_mailgun_data(mailgun_data):
    # Make sure we have what we need
    if not 'to' in mailgun_data or not 'from' in mailgun_data or not 'subject' in mailgun_data:
        raise MailgunException("Mailgun data missing FROM, TO, or SUBJECT!")
    logger.debug("dirty mailgun_data: %s" % mailgun_data)

    # Compile all our addresses
    from_name, from_address = email.utils.parseaddr(mailgun_data["from"])
    to_name, to_address = email.utils.parseaddr(mailgun_data["to"][0])
    exclude = [from_address, to_address]
    bccs = address_map(mailgun_data, "bcc", exclude)
    exclude.extend(list(bccs.keys()))
    # We do not want to remove our first 'to' address
    to_exclude = list(set(exclude))
    to_exclude.remove(to_address)
    tos = address_map(mailgun_data, "to", to_exclude)
    exclude.extend(list(tos.keys()))
    ccs = address_map(mailgun_data, "cc", exclude)

    # Repopulate our data with our clean lists
    mailgun_data["bcc"] = list(bccs.values())
    mailgun_data["cc"] = list(ccs.values())
    mailgun_data["to"] = list(tos.values())

    logger.debug("clean mailgun_data: %s" % mailgun_data)
    return mailgun_data


def inject_list_headers(mailgun_data):
    # Attach some headers: LIST-ID, REPLY-TO, Precedence...
    # Reply-To: list email apparently has some religious debates
    # (http://www.gnu.org/software/mailman/mailman-admin/node11.html)
    # Precedence: list - helps some out of office auto responders know not to send their auto-replies.
    to_name, to_address = email.utils.parseaddr(mailgun_data["to"][0])
    mailgun_data["h:List-Id"] = to_address
    mailgun_data["h:Reply-To"] = to_address
    mailgun_data["h:Precedence"] = "list"


def inject_footer(mailgun_data, public_url):
    text_footer = f"\n\n-------------------------------------------\n*~*~*~* Sent through Nadine *~*~*~*\n{public_url}"
    mailgun_data["text"] = mailgun_data["text"]  + text_footer
    if mailgun_data["html"]:
        html_footer = f"<br><br>-------------------------------------------<br>*~*~*~* Sent through Nadine *~*~*~*\n<br>{public_url}"
        mailgun_data["html"] = mailgun_data["html"] + html_footer


def mailgun_send(mailgun_data, files=None, clean_first=True, inject_list_id=True):
    if clean_first: clean_mailgun_data(mailgun_data)
    if inject_list_id: inject_list_headers(mailgun_data)

    # Make sure nothing goes out if the system is in debug mode
    if settings.DEBUG:
        if not hasattr(settings, 'MAILGUN_DEBUG') or settings.MAILGUN_DEBUG:
            # We will see this message in the mailgun logs but nothing will actually be delivered
            logger.debug("mailgun_send: setting testmode=yes")
            mailgun_data["o:testmode"] = "yes"

    mailgun_url = settings.MAILGUN_DOMAIN
    if not mailgun_url.startswith("http"):
        mailgun_url = "https://api.mailgun.net/v2/" + mailgun_url
    mailgun_url += "/messages"

    resp = requests.post(
        mailgun_url,
        auth=("api", settings.MAILGUN_API_KEY),
        data=mailgun_data,
        files=files,
    )
    logger.debug("Mailgun response: %s" % resp.text)
    return HttpResponse(status=200)


def validate_address(email_address):
    ''' Use the mailgun API to validate the given email address. '''
    if not hasattr(settings, "MAILGUN_API_KEY"):
        raise MailgunException("Missing required MAILGUN_API_KEY setting!")
    response = requests.get(
        "https://api.mailgun.net/v4/address/validate",
        auth=("api", settings.MAILGUN_API_KEY),
        params={"address": email_address}
    )
    if not response or not response.ok:
        raise MailgunException("Did not get an OK response from validation request")
    response_dict = json.loads(response.text)
    if not response_dict or 'risk' not in response_dict:
        raise MailgunException("Did not get expected JSON response")
    # Evaluate the risk.  Accept low and medium
    risk = response_dict['risk']
    logger.debug("validate_address: Risk for '%s' = '%s'" % (email_address, risk))
    return risk == 'low' or risk == 'medium'


def validate_address_v3(email_address):
    ''' Use the mailgun v3 API to validate the given email address. '''
    if not hasattr(settings, "MAILGUN_VALIDATION_KEY"):
        raise MailgunException("Missing required MAILGUN_VALIDATION_KEY setting!")
    response = requests.get(
        "https://api.mailgun.net/v3/address/validate",
        auth=("api", settings.MAILGUN_VALIDATION_KEY),
        params={"address": email_address}
    )
    if not response or not response.ok:
        raise MailgunException("Did not get an OK response from validation request")
    response_dict = json.loads(response.text)
    if not response_dict or 'is_valid' not in response_dict:
        raise MailgunException("Did not get expected JSON response")
    return response_dict['is_valid']


def api_get(uri, params=None):
    if not hasattr(settings, "MAILGUN_API_KEY"):
        raise MailgunException("Missing required MAILGUN_API_KEY setting!")
    if not params:
        params = {}

    response = requests.get(
        f"https://api.mailgun.net/v3/{uri}",
        auth=("api", settings.MAILGUN_API_KEY),
        params=params
    )
    print(response)
    if not response or not response.ok:
        raise MailgunException("Did not get an OK response from validation request")
    response_dict = json.loads(response.text)
    return response_dict


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
