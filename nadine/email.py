import mailchimp
import traceback
import logging
from datetime import datetime, time, date, timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.template import Template, TemplateDoesNotExist, Context
from django.core.mail import send_mail, EmailMessage
from django.contrib.auth.models import User
from django.utils import timezone

from nadine.utils.slack_api import SlackAPI
from nadine import mailgun

logger = logging.getLogger(__name__)


def valid_message_keys():
    return ["all", "introduction", "newsletter", "new_membership", "first_day_checkin",
            "exit_survey", "member_survey", "no_return", "checkin", "invalid_billing", "new_key",
            "no_signin", "no_device", "edit_profile", "slack_invite"]


def send_manual(user, message):
    message = message.lower()
    if not message in valid_message_keys():
        return False
    if message == "introduction" or message == "all":
        send_introduction(user)
    if message == "newsletter" or message == "all":
        subscribe_to_newsletter(user)
    if message == "new_member" or message == "all":
        send_new_membership(user)
    if message == "first_day_checkin" or message == "all":
        send_first_day_checkin(user)
    if message == "exit_survey" or message == "all":
        send_exit_survey(user)
    if message == "member_survey" or message == "all":
        send_member_survey(user)
    if message == "no_return_checkin" or message == "all":
        send_no_return_checkin(user)
    if message == "invalid_billing" or message == "all":
        send_invalid_billing(user)
    if message == "no_signin" or message == "all":
        send_no_signin(user)
    if message == "no_device" or message == "all":
        send_no_device(user)
    if message == "new_key" or message == "all":
        send_new_key(user)
    if message == "edit_profile" or message == "all":
        send_edit_profile(user)
    if message == "slack_invite":
        SlackAPI().invite_user(user)
    return True

#####################################################################
#                        Email Verification
#####################################################################

def send_verification(emailObj, request=None):
    """Send email verification link for this EmailAddress object.
    Raises smtplib.SMTPException, and NoRouteToHost.
    """
    html_template = get_template('email/verification_email.html')
    text_template = get_template('email/verification_email.txt')

    # Build our context
    site = get_current_site()
    context_dict = {
        'current_site': site.domain,
        'current_site_id': site.pk,
        'current_site_name': site.name,
        'emailaddress_id': emailObj.pk,
        'email': emailObj.email,
        'username': emailObj.user.username,
        'first_name': emailObj.user.first_name,
        'last_name': emailObj.user.last_name,
        'primary_email': emailObj.user.email,
        'verif_key': emailObj.verif_key,
    }
    verify_link = settings.EMAIL_VERIFICATION_URL % d
    d['verify_link'] = verify_link
    if request:
        context = RequestContext(request, d)
    else:
        context = Context(d)

    subject = ""
    msg = EmailMultiAlternatives(MM.VERIFICATION_EMAIL_SUBJECT % d,
        text_template.render(context),MM.FROM_EMAIL_ADDRESS,
        [self.email])
    msg.attach_alternative(html_template.render(context), 'text/html')
    msg.send(fail_silently=False)
    if MM.USE_MESSAGES:
        message = MM.VERIFICATION_LINK_SENT_MESSAGE % d
        if request is not None:
            messages.success(request, message,
                fail_silently=not MM.USE_MESSAGES)
        else:
            try:
                self.user.message_set.create(message=message)
            except AttributeError:
                pass # user.message_set is deprecated and has been
                     # fully removed as of Django 1.4. Thus, display
                     # of this message without passing in a view is
                     # supported only in 1.3


#####################################################################
#                        User Alerts
#####################################################################

def send_introduction(user):
    site = Site.objects.get_current()
    subject = "%s: Introduction to Nadine" % (site.name)
    message = render_to_string('email/introduction.txt', context={'user': user, 'site': site})
    send_quietly(user.email, subject, message)


def subscribe_to_newsletter(user):
    if settings.MAILCHIMP_NEWSLETTER_KEY:
        try:
            mc = mailchimp.Mailchimp(settings.MAILCHIMP_API_KEY)
            mc.lists.subscribe(id=settings.MAILCHIMP_NEWSLETTER_KEY, email={'email': user.email}, send_welcome=True)
        except:
            pass


def send_new_membership(user):
    site = Site.objects.get_current()
    membership = user.profile.last_membership()
    subject = "%s: New %s Membership" % (site.name, membership.membership_plan.name)
    message = render_to_string('email/new_membership.txt', context={'user': user, 'membership': membership, 'site': site})
    send(user.email, subject, message)
    announce_new_membership(user)


def send_first_day_checkin(user):
    site = Site.objects.get_current()
    subject = "%s: How was your first day?" % (site.name)
    message = render_to_string('email/first_day.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_exit_survey(user):
    site = Site.objects.get_current()
    subject = "%s: Exit Survey" % (site.name)
    message = render_to_string('email/exit_survey.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_member_survey(user):
    site = Site.objects.get_current()
    subject = "%s: Coworking Survey" % (site.name)
    message = render_to_string('email/member_survey.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_no_return_checkin(user):
    site = Site.objects.get_current()
    subject = "%s: Checking In" % (site.name)
    message = render_to_string('email/no_return.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_invalid_billing(user):
    site = Site.objects.get_current()
    subject = "%s: Billing Problem" % (site.name)
    message = render_to_string('email/invalid_billing.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_no_signin(user):
    site = Site.objects.get_current()
    subject = "%s: Forget to sign in?" % (site.name)
    message = render_to_string('email/no_signin.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_no_device(user):
    site = Site.objects.get_current()
    subject = "%s: Device Registration" % (site.name)
    message = render_to_string('email/no_device.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_new_key(user):
    site = Site.objects.get_current()
    subject = "%s: Key Holding Details" % (site.name)
    message = render_to_string('email/new_key.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)


def send_user_notifications(user, target):
    site = Site.objects.get_current()
    subject = "%s: %s is here!" % (site.name, target.get_full_name())
    message = render_to_string('email/user_notification.txt', context={'user': user, 'target': target, 'site': site})
    send(user.email, subject, message)


def send_contact_request(user, target):
    site = Site.objects.get_current()
    subject = "%s: %s wants to connect!" % (site.name, user.get_full_name())
    message = render_to_string('email/contact_request.txt', context={'user': user, 'target': target, 'site': site})
    send(target.email, subject, message)

def send_edit_profile(user):
    site = Site.objects.get_current()
    subject = "Please update your Nadine profile"
    message = render_to_string('email/edit_profile.txt', context={'user': user, 'site': site})
    send(user.email, subject, message)

#####################################################################
#                        System Alerts
#####################################################################


def announce_new_user(user):
    subject = "New User - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s just signed in for the first time! %s" % (user.get_full_name(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_free_trial(user):
    subject = "Free Trial - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s just signed in for the first time! %s" % (user.get_full_name(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_new_membership(user):
    membership = user.profile.last_membership()
    subject = "New %s: %s" % (membership.membership_plan.name, user.get_full_name())
    message = "Team,\r\n\r\n \t%s has a new %s membership! %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_member_checkin(user):
    membership = user.profile.last_membership()
    subject = "Member Check-in - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s has been a %s member for almost a month!  Someone go see how they are doing. %s" % (user.get_full_name(), membership.membership_plan.name, team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_need_photo(user):
    subject = "Photo Opportunity - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s just signed in and we don't have a photo of them yet. %s" % (user.get_full_name(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_billing_disable(user):
    subject = "Disabled Automatic Billing - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s just disabled their automatic billing through Nadine. %s" % (user.get_full_name(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_bad_email(user):
    subject = "Email Problem - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \tWe had a problem sending the introduction email to '%s'. %s" % (user.email, team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_anniversary(user):
    subject = "Anniversary - %s" % (user.get_full_name())
    duration = user.profile.duration_str()
    message = "Team,\r\n\r\n \t%s has been with us now for %s! %s" % (user.get_full_name(), duration, team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_new_key(user):
    subject = "New Key - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \t%s has been assigned a new key! %s" % (user.get_full_name(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def announce_special_day(user, special_day):
    subject = "Special Day - %s" % (user.get_full_name())
    message = "Team,\r\n\r\n \tToday is a special day for %s. Today is their %s! %s" % (user.get_full_name(), special_day.description.lower(), team_signature(user))
    send_quietly(settings.TEAM_EMAIL_ADDRESS, subject, message)


def manage_member_email(user):
    subject = "Email Problem - %s" % (user.get_full_name())
    c = Context({
        'user': user,
        'domain': Site.objects.get_current().domain,
    })
    text_content, html_content = mailgun.render_templates(c, "manage_member")
    logger.debug("text_context: %s" % text_content)
    logger.debug("html_content: %s" % html_content)

    mailgun_data = {"from": settings.EMAIL_ADDRESS,
                    #		"to": [settings.TEAM_EMAIL_ADDRESS, ],
                    "to": [settings.EMAIL_ADDRESS, ],
                    "subject": subject,
                    "text": text_content,
                    "html": html_content,
                    }
    mailgun.mailgun_send(mailgun_data)

#####################################################################
#                        Utilities
#####################################################################


def team_signature(user):
    site = Site.objects.get_current()
    return render_to_string('email/team_email_signature.txt', context={'user': user, 'site': site})

def send(recipient, subject, message):
    send_email(recipient, subject, message, False)

def send_quietly(recipient, subject, message):
    send_email(recipient, subject, message, True)

def send_email(recipient, subject, message, fail_silently):
    # A little safety net when debugging
    if settings.DEBUG:
        recipient = settings.EMAIL_ADDRESS

    note = None
    success = False
    try:
        msg = EmailMessage(subject, message, settings.EMAIL_ADDRESS, [recipient])
        # msg.content_subtype = "html"  # Main content is now text/html
        msg.send()
        success = True
    except:
        note = traceback.format_exc()
        if fail_silently:
            pass
        raise
    finally:
        user = User.objects.filter(email=recipient).first()
        try:
            from nadine.models.core import SentEmailLog
            log = SentEmailLog(user=user, member=user.profile, recipient=recipient, subject=subject, success=success)
            if note:
                log.note = note
            log.save()
        except:
            pass

# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
