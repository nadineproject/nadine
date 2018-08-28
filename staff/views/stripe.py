from django.views.generic.edit import BaseFormView
from django import forms
from django.http import Http404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, get_object_or_404

from django.contrib.auth.models import User
from django.contrib.admin.views.decorators import staff_member_required

from nadine.models.billing import StripeBillingProfile

import stripe


# TODO: Consider moving this into forms.py to follow Django app conventions.
class CheckoutForm(forms.Form):
    stripeToken = forms.CharField()
    stripeEmail = forms.EmailField()


@method_decorator(staff_member_required, name='dispatch')
class Checkout(BaseFormView):
    form_class = CheckoutForm
    # Limiting the role of this view as the form GET/render handling is elsewhere.
    http_method_names = ['post']

    def get_success_url(self):
        return reverse('staff:members:detail', kwargs={'username': self.kwargs['username']})

    def get_context_data(self, **kwargs):
        context = super(Checkout, self).get_context_data(**kwargs)
        # Ensure we have a user to associate Stripe customer with.
        if 'username' not in self.kwargs:
            raise Http404("username not provided")
        if 'user' not in context:
            context['user'] = get_object_or_404(User, username=self.kwargs['username'])
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        stripe_token = form.cleaned_data['stripeToken']
        stripe_customer_email = form.cleaned_data['stripeEmail']
        try:
            customer = stripe.Customer.create(source=stripe_token, email=stripe_customer_email)
            billingProfile = StripeBillingProfile(
                user=context['user'],
                customer_email=stripe_customer_email,
                customer_id=customer.id
            )
            billingProfile.save()
        except:
            # TODO: Handle Stripe Stripe Customer API failure cases (unfortunately these do not appear to be documented).
            # TODO: Handle StripeBillingProfile DB write failure cases.
            # TODO: At minimum, log something here.
            return redirect('staff:members:detail', username=self.kwargs['username'])

        return super().form_valid(form)

    def form_invalid(self, form):
        # TODO: This shouldn't really happen but we should still display/log an error.
        #       Need to determine what is available in Nadine to do this, eg: flash notifications?
        return redirect('staff:members:detail', username=self.kwargs['username'])