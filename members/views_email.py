from django.contrib import messages
from django.core.urlresolvers import reverse
from django.dispatch import Signal
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import View
from django.utils import timezone

from nadine.models.core import EmailAddress
from nadine import email

email_verified = Signal(providing_args=[])

class EmailVerify(View):

    def get(self, request, email_pk, verif_key):
        email_address = get_object_or_404(EmailAddress, pk=email_pk)
        if email_address.is_verified():
            messages.error(request, "Email address was already verified.")
        if email_address.verify_key != verify_key:
            messages.error(request, "Invalid key.")

        # Looks good!  Mark as verified
        email_address.remote_addr = request.META.get('REMOTE_ADDR')
        email_address.remote_host = request.META.get('REMOTE_HOST')
        email_address.verified_ts = timezone.now()
        email_address.save()
        email_verified.send_robust(sender=email_address)
        messages.success(request, "Email address has been verified.")
        
        next_url = settings.EMAIL_POST_VERIFY_URL
        if not next_url:
            next_url = reverse('member_profile', kwargs={'username': email_address.user.username})
        return redirect(next_url)


class SendLink(View):

    def get(self, request, email_pk, next=None):
        email = get_object_or_404(EmailAddress, pk=email_pk)
        if email.is_verified():
            messages.error(request, MM.EMAIL_ALREADY_VERIFIED_MESSAGE,
                fail_silently=not MM.USE_MESSAGES)
        else:
            email.send_verification(request=request)
        if next:
            return redirect(next)
        else:
            return redirect(request.META['HTTP_REFERER'])


def set_as_primary(request, email_pk):
    """Set the requested email address as the primary. Can only be
    requested by the owner of the email address."""
    email = get_object_or_404(EmailAddress, pk=email_pk)
    if not email.is_verified():
        messages.error(request, 'Email %s needs to be verified first.' % email)
    if email.user != request.user:
        messages.error(request, 'Invalid request.')
    elif email.is_verified():
        email.set_primary()
        messages.success(
            request, '%s is now marked as your primary email address.' % email
        )

    try:
        return redirect(request.META['HTTP_REFERER'])
    except KeyError:
        return redirect(reverse(MM.SET_AS_PRIMARY_REDIRECT))


def delete_email(request, email_pk):
    """Delete the given email. Must be owned by current user."""
    email = get_object_or_404(EmailAddress, pk=int(email_pk))
    if email.user == request.user:
        if not email.is_verified():
            email.delete()
        else:
            num_verified_emails = len(request.user.emailaddress_set.filter(
                verified_at__isnull=False))
            if num_verified_emails > 1:
                email.delete()
            elif num_verified_emails == 1:
                if MM.ALLOW_REMOVE_LAST_VERIFIED_EMAIL:
                    email.delete()
                else:
                    messages.error(request,
                        MM.REMOVE_LAST_VERIFIED_EMAIL_ATTEMPT_MSG,
                            extra_tags='alert-error')
    else:
        messages.error(request, 'Invalid request.')
    return redirect(MM.DELETE_EMAIL_REDIRECT)
