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
from django.template.loader import get_template, render_to_string
from django.template import Template, TemplateDoesNotExist
from django.utils import timezone

logger = logging.getLogger(__name__)


class MailgunException(Exception):
    pass

class MailgunMessage:

    def __init__(self, sender, receiver, subject, body_text=None):
        pass
        self.mailgun_data = {
            "from": sender,
            "to": [receiver, ],
            "cc": [],
            "bcc": [],
            "subject": subject,
        }
        if body_text:
            self.add_text_body(body_text)

    def add_to(self, address):
        self.mailgun_data["to"].append(address)

    def add_cc(self, address):
        self.mailgun_data["cc"].append(address)

    def add_bcc(self, address):
        self.mailgun_data["bcc"].append(address)

    def add_text_body(self, body_text):
        self.mailgun_data["text"] = body_text

    def add_html_body(self, body_html):
        self.mailgun_data["html"] = body_html

    def set_debug(self, debug):
        if debug:
            self.mailgun_data["o:testmode"] = "yes"
        elif "o:testmode" in self.mailgun_data:
            del self.mailgun_data["o:testmode"]

    def _address_map(self, key, exclude=None):
        if not exclude: exclude = []
        a_map = OrderedDict()
        if key in self.mailgun_data:
            for a in self.mailgun_data[key]:
                name, address = email.utils.parseaddr(a)
                if not address in exclude:
                    a_map[address.lower()] = a
        return a_map

    def _clean_data(self):
        logger.debug("dirty data: %s" % self.mailgun_data)

        # Compile all our addresses
        from_name, from_address = email.utils.parseaddr(self.mailgun_data["from"])
        to_name, to_address = email.utils.parseaddr(self.mailgun_data["to"][0])
        exclude = [from_address, to_address]
        bccs = address_map(self.mailgun_data, "bcc", exclude)
        exclude.extend(list(bccs.keys()))
        # We do not want to remove our first 'to' address
        to_exclude = list(set(exclude))
        to_exclude.remove(to_address)
        tos = address_map(self.mailgun_data, "to", to_exclude)
        exclude.extend(list(tos.keys()))
        ccs = address_map(self.mailgun_data, "cc", exclude)

        # Repopulate our data with our clean lists
        self.mailgun_data["bcc"] = list(bccs.values())
        self.mailgun_data["cc"] = list(ccs.values())
        self.mailgun_data["to"] = list(tos.values())

        logger.debug("clean data: %s" % self.mailgun_data)
        return self.mailgun_data

    def get_mailgun_data(self, clean_first=True):
        # Make sure we have what we need
        if not "to" in self.mailgun_data or not "from" in self.mailgun_data:
            raise MailgunException("Mailgun data missing TO/FROM!")
        if not "subject" in self.mailgun_data:
            raise MailgunException("Mailgun data missing SUBJECT!")
        if not "text" in self.mailgun_data and not "html" in self.mailgun_data:
            raise MailgunException("Message has no body!")

        if clean_first:
            return self._clean_data()
        return self.mailgun_data

class MailgunAPI:

    MESSAGES = "/messages"
    STATS_TOTAL = "/stats/total"

    def __init__(self):
        self.domain = getattr(settings, 'MAILGUN_DOMAIN', None)
        if not self.domain:
            raise ImproperlyConfigured("Please set your MAILGUN_DOMAIN setting.")

        self.api_key = getattr(settings, 'MAILGUN_API_KEY', None)
        if not self.api_key:
            raise ImproperlyConfigured("Please set your MAILGUN_API_KEY setting.")

        self.debug = getattr(settings, 'MAILGUN_DEBUG', True)

        self.base_url = self.domain
        if not self.base_url.startswith("http"):
            self.base_url = "https://api.mailgun.net/v3/" + self.base_url
        if self.base_url.endswith("/"):
            self.base_url = self.base_url[:-1]

    def validate_address(self, address):
        ''' Use the mailgun API to validate the given email address. '''
        response = requests.get(
            "https://api.mailgun.net/v4/address/validate",
            auth=("api", self.api_key),
            params={"address": address}
        )
        if not response or not response.ok:
            raise MailgunException("Did not get an OK response from validation request")
        response_dict = response.json()
        if not response_dict or 'risk' not in response_dict:
            raise MailgunException("Did not get expected JSON response")

        # Evaluate the risk.  Accept low and medium
        risk = response_dict['risk']
        logger.debug("validate_address: Risk for '%s' = '%s'" % (address, risk))
        return risk == 'low' or risk == 'medium'

    def send(self, mailgun_data, files=None, clean_first=True, inject_list_id=True):
        if clean_first: clean_mailgun_data(mailgun_data)
        if inject_list_id: inject_list_headers(mailgun_data)

        # Make sure nothing goes out if the system is in debug mode
        if self.debug:
            # We will see this message in the mailgun logs but nothing will actually be delivered
            logger.debug("mailgun_send: setting testmode=yes")
            mailgun_data["o:testmode"] = "yes"

        mailgun_url = self.base_url + self.MESSAGES

        response = requests.post(
            mailgun_url,
            auth =("api", self.api_key),
            data = mailgun_data,
            files = files,
        )
        logger.debug("Mailgun response: %s" % response.text)
        if not response or not response.ok:
            raise MailgunException("Did not get an OK response")

        return HttpResponse(status=200)

    def get(self, uri, params=None):
        if not params: params = {}

        if not uri:
            raise MailgunException("Invalid URI")
        if not uri.startswith("/"):
            uri = "/" + uri
        mailgun_url = self.base_url + uri
        logger.debug("Mailgun URL: %s" % mailgun_url)
        logger.debug("Mailgun Params: %s" % params)

        response = requests.get(
            mailgun_url,
            auth=("api", settings.MAILGUN_API_KEY),
            params=params
        )
        logger.debug("Mailgun response(%d): %s" % (response.status_code, response.text))
        response_dict = response.json()
        if not response.ok:
            if 'message' in response_dict:
                raise MailgunException(response_dict['message'])
            else:
                raise MailgunException("Did not get an OK response")

        return response_dict


################################################################################
# Helper Methods
################################################################################


def get_stats_delivered():
    # Defaults to last 7 days
    # TODO - Take time parameters
    return api.get(MailgunAPI.STATS_TOTAL, params={"event": "delivered"})


def get_stats_failed():
    # Defaults to last 7 days
    # TODO - Take time parameters
    return api.get(MailgunAPI.STATS_TOTAL, params={"event": "failed"})


################################################################################
# Deprecated Methods
################################################################################


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


def send_template(template, to, subject, context=None):
    if not context:
        context = {}
    context["to"] = to
    context["site_name"] = settings.SITE_NAME
    context["site_url"] = "%s://%s" % (settings.SITE_PROTO, settings.SITE_DOMAIN)

    # Render our body text
    body_text = render_to_string(template, context=context)
    mailgun_data = {
        "from": settings.DEFAULT_FROM_EMAIL,
        "to": [to, ],
        "subject": subject,
        "text": body_text,
    }

    # Fire in the hole!
    mailgun_send(mailgun_data)


# Copyright 2020 Office Nomads LLC (https://officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at https://opensource.org/licenses/Apache-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
