from datetime import date, datetime, timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, Http404, HttpRequest
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.template import Template, Context, RequestContext

from nadine import email
from nadine.utils import mailgun
from nadine.models.core import UserProfile, Membership
from nadine.models.usage import CoworkingDay
#from nadine.models.resource import Room
#from nadine.models.payment import Transaction
from nadine.models.alerts import MemberAlert
from nadine.forms import MemberSearchForm, NewUserForm, EditProfileForm
from members.models import HelpText


######################################################################
# User Tests
######################################################################


def is_active_member(user):
    if user and not user.is_anonymous():
        # If today is their Free Trial Day count them as active
        if CoworkingDay.objects.filter(user=user, payment='Trial', visit_date=date.today()).count() == 1:
            return True

        # Check to make sure their currently an active member
        return user.profile.is_active()

    # No user, no profile, no active
    return False


def is_manager(user):
    if user and not user.is_anonymous():
        return user.profile.is_manager()
    return False


def is_new_user(user):
    # also check for staff and if settings allow registration
    if user.is_anonymous() or user.profile.is_manager():
        if settings.ALLOW_ONLINE_REGISTRATION == True:
            return True

    return False


######################################################################
#  Core Views
######################################################################


def not_active(request):
    return render(request, 'members/not_active.html', {'settings': settings})


@login_required
def home(request):
    title = "Home"
    template_text = "Welcome to {{ site.name }}"
    other_topics = {}
    for topic in HelpText.objects.all():
        if topic.slug == 'home':
            title = topic.title
            template_text = topic.template
        else:
            other_topics[topic.title] = topic

    current_context = RequestContext(request)
    template = Template(template_text)
    rendered = template.render(current_context)
    context = {'title': title, 'page_body': rendered, 'other_topics': other_topics, 'settings': settings}
    return render(request, 'members/home.html', context)


# TODO - evaluate.  Too similar to home
@login_required
def faq(request):
    title = "faq"
    template_text = "Frequently Asked Questions"
    other_topics = {}
    for topic in HelpText.objects.all():
        if topic.slug == 'faq':
            title = topic.title
            template_text = topic.template
        else:
            other_topics[topic.title] = topic

    current_context = RequestContext(request)
    template = Template(template_text)
    rendered = template.render(current_context)

    context = {'title': title, 'page_body': rendered,
        'other_topics': other_topics, 'settings': settings}
    return render(request, 'members/faq.html', context)


@login_required
def help_topic(request, slug):
    topic = get_object_or_404(HelpText, slug=slug)
    title = topic.title
    template_text = topic.template
    other_topics = HelpText.objects.all().order_by('order')
    current_context = context_instance = RequestContext(request)
    template = Template(template_text)
    rendered = template.render(current_context)
    context = {'title': title, 'page_body': rendered,
        'other_topics': other_topics, 'settings': settings}
    return render(request, 'members/help_topic.html', context)


@login_required
@user_passes_test(is_active_member, login_url='member_not_active')
def view_members(request):
    active_members = User.helper.active_members().order_by('first_name')
    here_today = User.helper.here_today()
    has_key = has_mail = None
    if request.user.profile.is_manager():
        has_key = User.helper.members_with_keys()
        has_mail = User.helper.members_with_mail()

    search_terms = None
    search_results = None
    if request.method == "POST":
        search_form = MemberSearchForm(request.POST)
        if search_form.is_valid():
            search_terms = search_form.cleaned_data['terms']
            search_results = User.helper.search(search_terms, True)
    else:
        search_form = MemberSearchForm()

    context = {'settings': settings, 'active_members': active_members,
        'here_today': here_today, 'search_results': search_results,
        'search_form': search_form, 'search_terms': search_terms,
        'has_key': has_key, 'has_mail': has_mail}
    return render(request, 'members/view_members.html', context)


@csrf_exempt
@login_required
@user_passes_test(is_manager, login_url='member_not_active')
def manage_member(request, username):
    user = get_object_or_404(User, username=username)

    # Handle the buttons if a task is being marked done
    if request.method == 'POST':
        #print(request.POST)
        if 'resolve_task' in request.POST:
            alert = MemberAlert.objects.get(pk=request.POST.get('alert_id'))
            alert.resolve(request.user)

    # Render the email content in to a variable to make up the page content
    text_content, html_content = mailgun.get_manage_member_content(user)

    return render(request, 'members/manage_member.html', {'user': user, 'page_content': html_content})


@user_passes_test(is_new_user, login_url='member_home')
def register(request):
    page_message = None
    if request.method == 'POST':
        registration_form = NewUserForm(request.POST)
        profile_form = EditProfileForm(request.POST, request.FILES)
        try:
            if request.POST.get('password-create') == request.POST.get('password-confirm'):
                if registration_form.is_valid():
                    user = registration_form.save()

                    registration = get_object_or_404(UserProfile, user=user)
                    registration.address1 = request.POST.get('address1', None)
                    registration.phone =  request.POST.get('phone', None)
                    registration.phone2 = request.POST.get('phone2', None)
                    registration.address2 = request.POST.get('address2', None)
                    registration.city = request.POST.get('city', None)
                    registration.state = request.POST.get('state', None)
                    registration.zipcode = request.POST.get('zipcode', None)
                    registration.bio = request.POST.get('bio', None)
                    registration.gender = request.POST.get('gender', None)
                    # TODO needs to be an instance of these three?
                    # registration.howHeard = request.POST.get('howHeard', None)
                    # registration.industry = request.POST.get('industry', None)
                    # registration.neighborhood = request.POST.get('neighborhood', None)
                    registration.has_kids = request.POST.get('has_kids', None)
                    registration.self_employed = request.POST.get('self_employed', None)
                    registration.company_name = request.POST.get('company_name', None)
                    registration.public_profile = request.POST.get('public_profile', False)
                    registration.photo = request.FILES.get('photo', None)

                    registration.save()

                    pwd = request.POST.get('password-create')
                    u = User.objects.get(username=user.username)
                    u.set_password(pwd)
                    u.save()

                    return HttpResponseRedirect(reverse('member_profile', kwargs={'username': user.username}))
            else:
                page_message = 'The entered passwords do not match. Please try again.'
        except Exception as e:
            page_message = str(e)
            logger.error(str(e))
    else:
        registration_form = NewUserForm()
        profile_form = EditProfileForm()

    context = {'registration_form': registration_form, 'page_message': page_message,
        'ALLOW_PHOTO_UPLOAD': settings.ALLOW_PHOTO_UPLOAD,
        'settings': settings, 'profile_form': profile_form}
    return render(request, 'members/register.html', context)


# Copyright 2016 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
