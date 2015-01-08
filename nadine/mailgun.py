import json
import requests
import datetime
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)

def mailgun_send(list_address, mailgun_data, files_dict=None):
	logger.debug("Mailgun send: %s" % mailgun_data)
	logger.debug("Mailgun files: %s" % files_dict)
	
	if settings.DEBUG:
		if not hasattr(settings, 'MAILGUN_DEBUG') or settings.MAILGUN_DEBUG:
			# We will see this message in the mailgun logs but nothing will actually be delivered
			logger.debug("mailgun_send: setting testmode=yes")
			mailgun_data["o:testmode"] = "yes"

	# attach some headers: LIST-ID, REPLY-TO, MSG-ID, precedence...
	# Precedence: list - helps some out of office auto responders know not to send their auto-replies. 
	mailgun_data["h:List-Id"] = list_address
	mailgun_data["h:Precedence"] = "list"
		
	# Reply-To: list email apparently has some religious debates
	# (http://www.gnu.org/software/mailman/mailman-admin/node11.html) 
	# but seems to be common these days 
	mailgun_data["h:Reply-To"] = list_address

	resp = requests.post("https://api.mailgun.net/v2/%s/messages" % settings.MAILGUN_DOMAIN,
		auth=("api", settings.MAILGUN_API_KEY),
		data=mailgun_data, 
		files=files_dict
	)
	logger.debug("Mailgun response: %s" % resp.text)
	return HttpResponse(status=200)

def clean_incoming(request):
	if not request.POST:
		return None

	header_txt = request.POST.get('message-headers')
	message_headers = json.loads(header_txt)
	message_header_keys = [item[0] for item in message_headers]
	
	# A List-Id header will only be present if it has been added manually in
	# this function, ie, if we have already processed this message. 
	if request.POST.get('List-Id') or 'List-Id' in message_header_keys:
		# mailgun requires a code 200 or it will continue to retry delivery
		logger.debug('List-Id header was found! Dropping message silently')
		return None

	# If 'Auto-Submitted' in message_headers or message_headers['Auto-Submitted'] != 'no':
	if 'Auto-Submitted' in message_header_keys: 
		logger.info('message appears to be auto-submitted. reject silently')
		return None

	# Pull the variables out of the POST
	recipient = request.POST.get('recipient')
	from_address = request.POST.get('from')
	subject = request.POST.get('subject')
	body_plain = request.POST.get('body-plain')
	body_html = request.POST.get('body-html')

	# Prefix subject
	# but only if the prefix string isn't already in the subject line (such as a reply)
	#if subject.find(location.email_subject_prefix) < 0:
	#	prefix = "["+location.email_subject_prefix + "] " 
	#	subject = prefix + subject
	#logger.debug("subject: %s" % subject)

	# Add in a footer
	text_footer = "\n\n-------------------------------------------\n*~*~*~* Sent through Nadine *~*~*~* "
	body_plain = body_plain + text_footer
	if body_html:
		html_footer = "<br><br>-------------------------------------------<br>*~*~*~* Sent through Nadine *~*~*~* "
		body_html = body_html + html_footer

	# Build and return our data
	mailgun_data =  {"from": from_address,
		"to": [recipient, ],
		"subject": subject,
		"text": body_plain,
		"html": body_html,
	}
	return mailgun_data

@csrf_exempt
def staff(request):
	mailgun_data = clean_incoming(request)
	if not mailgun_data:
		# Reject silently
		return HttpResponse(status=200)

	# Build our BCC list
	# Remove duplicates and the sender
	bcc_list = []
	sender = request.POST.get('sender')
	for user in User.objects.filter(is_staff=True, is_active=True):
		if user.email not in bcc_list:
			bcc_list.append(user.email)
	if sender in bcc_list:
		bcc_list.remove(sender)
	logger.debug("bcc list: %s" % bcc_list)
	mailgun_data[bcc] = bcc_list

	attachments = []
	for attachment in request.FILES.values():
		attachments.append(("inline", attachment))

	# Send the message 
	list_address = "staff@%s" % settings.MAILGUN_DOMAIN
	return mailgun_send(list_address, mailgun_data, attachments)
	
# mailgun setup example
# match_recipient("test80085@(?P<location>.*?).mail.embassynetwork.com")
# forward("https://embassynetwork.com/locations/\g<location>/email/test80085")

@csrf_exempt
def test80085(request):
	mailgun_data = clean_incoming(request)
	if not mailgun_data:
		# Reject silently
		return HttpResponse(status=200)

	bcc_list = ['jsayles@gmail.com', 'jessy@jessykate.com']
	logger.debug("bcc list: %s" % bcc_list)

	attachments = []
	for attachment in request.FILES.values():
		attachments.append(("inline", attachment))

	# Send the message 
	list_address = "test80085@%s" % settings.MAILGUN_DOMAIN
	return mailgun_send(list_address, mailgun_data, attachments)