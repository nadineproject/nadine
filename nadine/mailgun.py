import json
import requests
import datetime
import logging
import email.utils

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
from django.views.decorators.csrf import csrf_exempt
from staff.models import Member

logger = logging.getLogger(__name__)

class MailgunException(Exception):
	pass

def render_templates(context, email_key):
	text_content = None
	html_content = None

	try:
		text_template = get_template("emails/%s.txt" % email_key)
		if text_template:
			text_content = text_template.render(context)

		html_template = get_template("emails/%s.html" % email_key)
		if html_template:
			html_content = html_template.render(context)
	except TemplateDoesNotExist:
		pass

	return (text_content, html_content)

def mailgun_send(mailgun_data, files_dict=None):
	#logger.debug("Mailgun send: %s" % mailgun_data)
	#logger.debug("Mailgun files: %s" % files_dict)

	# Make sure we have what we need
	from_name, from_address = email.utils.parseaddr(mailgun_data["from"])
	to_name, to_address = email.utils.parseaddr(mailgun_data["to"][0])
	subject = mailgun_data["subject"]
	if not from_address or not to_address or not subject:
		raise MailgunException("Mailgun data missing FROM, TO, or SUBJECT!")
	logger.debug("from: %s, to: %s, subject: %s" % (from_address, to_address, subject))

	# Clean up our bcc list
	if "bcc" in mailgun_data:
		bcc_list = mailgun_data["bcc"]
		if from_address in bcc_list:
			bcc_list.remove(from_address)
		if to_address in bcc_list:
			bcc_list.remove(to_address)
		mailgun_data["bcc"] = list(set(bcc_list))
		logger.debug("bcc: %s" % mailgun_data["bcc"])

	# Attach some headers: LIST-ID, REPLY-TO, Precedence...
	# Reply-To: list email apparently has some religious debates
	# (http://www.gnu.org/software/mailman/mailman-admin/node11.html) 
	# Precedence: list - helps some out of office auto responders know not to send their auto-replies. 
	mailgun_data["h:List-Id"] = to_address
	mailgun_data["h:Reply-To"] = to_address
	mailgun_data["h:Precedence"] = "list"

	# Make sure nothign goes out if the system is in debug mode
	if settings.DEBUG:
		if not hasattr(settings, 'MAILGUN_DEBUG') or settings.MAILGUN_DEBUG:
			# We will see this message in the mailgun logs but nothing will actually be delivered
			logger.debug("mailgun_send: setting testmode=yes")
			mailgun_data["o:testmode"] = "yes"

	# Fire in the hole!
	resp = requests.post("https://api.mailgun.net/v2/%s/messages" % settings.MAILGUN_DOMAIN,
		auth=("api", settings.MAILGUN_API_KEY),
		data=mailgun_data, 
		files=files_dict
	)
	logger.debug("Mailgun response: %s" % resp.text)
	return HttpResponse(status=200)

def clean_incoming(request):
	if not request.POST:
		raise MailgunException("Request not a POST!")

	header_txt = request.POST.get('message-headers')
	message_headers = json.loads(header_txt)
	message_header_keys = [item[0] for item in message_headers]
	
	# A List-Id header will only be present if it has been added manually in
	# this function, ie, if we have already processed this message. 
	if request.POST.get('List-Id') or 'List-Id' in message_header_keys:
		raise MailgunException("List-Id header was found!")

	# If 'Auto-Submitted' in message_headers or message_headers['Auto-Submitted'] != 'no':
	if 'Auto-Submitted' in message_header_keys: 
		raise MailgunException("Message appears to be auto-submitted")

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
	
	attachments = []
	for attachment in request.FILES.values():
		attachments.append(("inline", attachment))

	return (mailgun_data, attachments)

@csrf_exempt
def staff(request):
	try:
		mailgun_data, attachments = clean_incoming(request)
	except MailgunException as e:
		# mailgun requires a code 200 or it will continue to retry delivery
		return HttpResponse(status=200)

	# Hard code the recipient to be this address
	mailgun_data["to"] = ["staff@%s" % settings.MAILGUN_DOMAIN, ]

	# Going out to all Users that are active and staff
	mailgun_data["bcc"] = User.objects.filter(is_staff=True, is_active=True)

	# Send the message 
	return mailgun_send(mailgun_data, attachments)

@csrf_exempt
def team(request):
	try:
		mailgun_data, attachments = clean_incoming(request)
	except MailgunException as e:
		# mailgun requires a code 200 or it will continue to retry delivery
		return HttpResponse(status=200)

	# Hard code the recipient to be this address
	mailgun_data["to"] = ["team@%s" % settings.MAILGUN_DOMAIN, ]

	# Goes out to all managers
	mailgun_data["bcc"] = Member.objects.managers(include_future=True)

	# Send the message 
	return mailgun_send(mailgun_data, attachments)
	
# mailgun setup example
# match_recipient("test80085@(?P<location>.*?).mail.embassynetwork.com")
# forward("https://embassynetwork.com/locations/\g<location>/email/test80085")
@csrf_exempt
def test80085(request):
	try:
		mailgun_data, attachments = clean_incoming(request)
	except MailgunException as e:
		# mailgun requires a code 200 or it will continue to retry delivery
		return HttpResponse(status=200)

	mailgun_data["to"] = ["test80085@%s" % settings.MAILGUN_DOMAIN, ]
	mailgun_data["bcc"] = ['jsayles@gmail.com']
	return mailgun_send(mailgun_data, attachments)