from datetime import datetime, time, date, timedelta
from django.contrib.sites.models import Site
from django.template.loader import render_to_string
from django.core.mail import send_mail
from models import Member, DailyLog
import settings

def send_introduction(user):
	site = Site.objects.get_current()
	subject = "%s: Introduction to Nadine" % (site.name)
	message = render_to_string('email/introduction.txt', {'user':user, 'site':site})
	send_mail(subject, message, settings.EMAIL_ADDRESS, [user.email], fail_silently=False)	

def send_end_of_day_checkin():
	site = Site.objects.get_current()
	subject = "%s: Thanks for stopping by!" % (site.name)
	now = datetime.now()
	midnight = now - timedelta(seconds=now.hour*60*60 + now.minute*60 + now.second)
	free_trials = DailyLog.objects.filter(visit_date__range=(midnight, now), payment='Trial')
	for l in free_trials:
		user = l.member.user
		message = render_to_string('email/end_of_day.txt', {'user':user, 'site':site})
		send_mail(subject, message, settings.EMAIL_ADDRESS, [user.email], fail_silently=False)

def send_invalid_billing(user):
	site = Site.objects.get_current()
	subject = "%s: Billing Problem" % (site.name)
	message = render_to_string('email/invalid_billing.txt', {'user':user, 'site':site})
	send_mail(subject, message, settings.EMAIL_ADDRESS, [user.email], fail_silently=False)	

	

