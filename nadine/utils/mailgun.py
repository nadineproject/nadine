from __future__ import absolute_import

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
from django.template import Template, TemplateDoesNotExist, Context
from django.template.loader import get_template
from django.contrib.sites.models import Site
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
    exclude.extend(bccs.keys())
    # We do not want to remove our first 'to' address
    to_exclude = list(set(exclude))
    to_exclude.remove(to_address)
    tos = address_map(mailgun_data, "to", to_exclude)
    exclude.extend(tos.keys())
    ccs = address_map(mailgun_data, "cc", exclude)

    # Repopulate our data with our clean lists
    mailgun_data["bcc"] = bccs.values()
    mailgun_data["cc"] = ccs.values()
    mailgun_data["to"] = tos.values()

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


def mailgun_send(mailgun_data, files=None, clean_first=True, inject_list_id=True):
    if clean_first: clean_mailgun_data(mailgun_data)
    if inject_list_id: inject_list_headers(mailgun_data)

    # Make sure nothing goes out if the system is in debug mode
    if settings.DEBUG:
        if not hasattr(settings, 'MAILGUN_DEBUG') or settings.MAILGUN_DEBUG:
            # We will see this message in the mailgun logs but nothing will actually be delivered
            logger.debug("mailgun_send: setting testmode=yes")
            mailgun_data["o:testmode"] = "yes"

    resp = requests.post("https://api.mailgun.net/v2/%s/messages" % settings.MAILGUN_DOMAIN,
                         auth=("api", settings.MAILGUN_API_KEY),
                         data=mailgun_data,
                         files=files
                         )
    logger.debug("Mailgun response: %s" % resp.text)
    return HttpResponse(status=200)


# TODO - move to email?
def send_manage_member(user, subject=None):
    if subject == None:
        subject = "Incomplete Tasks"
    # Adjust the subject if we have a prefix
    if hasattr(settings, "EMAIL_SUBJECT_PREFIX"):
        subject = settings.EMAIL_SUBJECT_PREFIX.strip() + " " + subject.strip()

    subject = "%s - %s" % (subject, user.get_full_name())
    text_content, html_content = get_manage_member_content(user)
    mailgun_data = {"from": settings.EMAIL_ADDRESS,
                    "to": [settings.TEAM_EMAIL_ADDRESS, ],
                    "subject": subject,
                    "text": text_content,
                    "html": html_content,
                    }
    return mailgun_send(mailgun_data, inject_list_id=False)


def render_templates(context, email_key):
    text_content = None
    html_content = None

    try:
        text_template = get_template("email/%s.txt" % email_key)
        if text_template:
            text_content = text_template.render(context)

        html_template = get_template("email/%s.html" % email_key)
        if html_template:
            html_content = html_template.render(context)
    except TemplateDoesNotExist:
        pass

    #logger.debug("text_context: %s" % text_content)
    #logger.debug("html_content: %s" % html_content)
    return (text_content, html_content)


def get_manage_member_content(user):
    if settings.DEBUG:
        site_url = ''
    else:
        site_url = "https://" + Site.objects.get_current().domain
    c = Context({
        'today': timezone.localtime(timezone.now()),
        'user': user,
        'site_url': site_url,
    })
    return render_templates(c, "manage_member")


# Deprecated and moved to clean_mailgun_data
# TODO - remove
# def clean_incoming(request):
#     if not request.POST:
#         raise MailgunException("Request not a POST!")
#
#     header_txt = request.POST.get('message-headers')
#     message_headers = json.loads(header_txt)
#     message_header_keys = [item[0] for item in message_headers]
#
#     # A List-Id header will only be present if it has been added manually in
#     # this function, ie, if we have already processed this message.
#     if request.POST.get('List-Id') or 'List-Id' in message_header_keys:
#         raise MailgunException("List-Id header was found!")
#
#     # If 'Auto-Submitted' in message_headers or message_headers['Auto-Submitted'] != 'no':
#     if 'Auto-Submitted' in message_header_keys:
#         raise MailgunException("Message appears to be auto-submitted")
#
#     # Pull the variables out of the POST
#     recipient = request.POST.get('recipient')
#     from_address = request.POST.get('from')
#     subject = request.POST.get('subject')
#     body_plain = request.POST.get('body-plain')
#     body_html = request.POST.get('body-html')
#     logger.debug("Incoming from: %s, to: %s, subject: %s" % (from_address, recipient, subject))
#
#     # Add in a footer
#     text_footer = "\n\n-------------------------------------------\n*~*~*~* Sent through Nadine *~*~*~* "
#     body_plain = body_plain + text_footer
#     if body_html:
#         html_footer = "<br><br>-------------------------------------------<br>*~*~*~* Sent through Nadine *~*~*~* "
#         body_html = body_html + html_footer
#
#     # Build and return our data
#     mailgun_data = {"from": from_address,
#                     "to": [recipient, ],
#                     "subject": subject,
#                     "text": body_plain,
#                     "html": body_html,
#                     }
#
#     attachments = []
#     for attachment in request.FILES.values():
#         attachments.append(("inline", attachment))
#
#     return (mailgun_data, attachments)
#
#
# Deprecated and moved to comlink
# TODO - remove all 3
# @csrf_exempt
# def staff(request):
#     try:
#         mailgun_data, attachments = clean_incoming(request)
#     except MailgunException as e:
#         # mailgun requires a code 200 or it will continue to retry delivery
#         return HttpResponse(status=200)
#
#     # Pull the list this should go to and set them in the BCC
#     # Going out to all Users that are active and staff
#     bcc_list = list(User.objects.filter(is_staff=True, is_active=True).values_list('email', flat=True))
#     mailgun_data["bcc"] = bcc_list
#
#     # This goes out to staff and anyone that isn't already in the BCC list
#     to_list = ["staff@%s" % settings.MAILGUN_DOMAIN, ]
#     for to in mailgun_data["to"]:
#         if not to in bcc_list:
#             to_list.append(to)
#     mailgun_data["to"] = to_list
#
#     # Send the message
#     return mailgun_send(mailgun_data, attachments)
#
# @csrf_exempt
# def team(request):
#     try:
#         mailgun_data, attachments = clean_incoming(request)
#     except MailgunException as e:
#         # mailgun requires a code 200 or it will continue to retry delivery
#         return HttpResponse(status=200)
#
#     # Goes out to all managers
#     bcc_list = list(User.helper.managers(include_future=True).values_list('email', flat=True))
#     mailgun_data["bcc"] = bcc_list
#
#     # Hard code the recipient to be this address
#     to_list = ["team@%s" % settings.MAILGUN_DOMAIN, ]
#     for to in mailgun_data["to"]:
#         if not to in bcc_list:
#             to_list.append(to)
#     mailgun_data["to"] = to_list
#
#     # Send the message
#     return mailgun_send(mailgun_data, attachments)
#
# @csrf_exempt
# def test(request):
#     print("Request: ")
#     print(request)
#
#     try:
#         mailgun_data, attachments = clean_incoming(request)
#     except MailgunException as e:
#         # mailgun requires a code 200 or it will continue to retry delivery
#         return HttpResponse(status=200)
#
#     mailgun_data["to"] = ["test80085@%s" % settings.MAILGUN_DOMAIN, ]
#     mailgun_data["bcc"] = ['jsayles@gmail.com']
#     #return mailgun_send(mailgun_data, attachments)
#     return HttpResponse(status=200)
