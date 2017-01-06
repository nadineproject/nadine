from __future__ import unicode_literals

import logging
import traceback
from datetime import datetime, timedelta, date
from collections import OrderedDict

from django.db import models
from django.db.models import Q
from django.core import urlresolvers
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User

from nadine.models.core import Website, URLType
from nadine.models.membership import Membership, Membership2

from taggit.managers import TaggableManager

logger = logging.getLogger(__name__)


class OrganizationManager(models.Manager):

    def active_organizations(self, on_date=None):
        """ Organizations of all active members """
        # TODO - This whole method will be rewritten when
        # we change up how memberships are handled --JLS
        if not on_date:
            on_date = timezone.now().date()
        org_ids = []
        for m in Membership.objects.active_memberships(on_date):
            for o in m.user.profile.active_organizations():
                org_ids.append(o.id)
        return Organization.objects.filter(id__in=org_ids)

    def with_tag(self, tag):
        return self.active_organizations().filter(tags__name__in=[tag])

    def search(self, search_string):
        if len(search_string) == 0:
            return None

        org_query = Organization.objects.all()
        name_query = Q(name__icontains=search_string)

        org_query = org_query.filter(name_query).order_by('name')

        return org_query.order_by('name')

def org_photo_path(instance, filename):
    ext = filename.split('.')[-1]
    return "org_photos/%s.%s" % (instance.name, ext.lower())


class Organization(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="+")
    name = models.CharField(max_length=64, unique=True)
    lead = models.ForeignKey(User, null=True, blank=True)
    blurb = models.CharField(max_length=112, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to=org_photo_path, blank=True, null=True)
    public = models.BooleanField(default=False)
    locked = models.BooleanField(default=False)
    tags = TaggableManager(blank=True)
    websites = models.ManyToManyField(Website, blank=True)

    objects = OrganizationManager()

    def members(self, on_date=None):
        active = self.active_memberships(on_date)
        return User.objects.filter(id__in=active.values('user'))

    def active_memberships(self, on_date=None):
        if not on_date:
            on_date = timezone.now().date()
        future = Q(end_date__isnull=True)
        unending = Q(end_date__gte=on_date)
        return self.organizationmember_set.filter(start_date__lte=on_date).filter(future | unending)

    def active_membership(self, user, on_date=None):
        """ Active org membership for this user """
        if not on_date:
            on_date = timezone.now().date()
        for m in self.organizationmember_set.filter(user=user):
            if m.is_active(on_date):
                return m
        return None

    def has_member(self, user, on_date=None):
        if not on_date:
            on_date = timezone.now().date()
        m = self.active_membership(user, on_date)
        return m is not None

    def add_member(self, user, start_date=None, end_date=None):
        if not start_date:
            start_date = timezone.now().date()
        if self.has_member(user, start_date):
            raise Exception("User already a member")
        return OrganizationMember.objects.create(organization=self, user=user,
            start_date=start_date, end_date=end_date)

    def can_edit(self, user):
        m = self.active_membership(user)
        if not m:
            return False
        return not self.locked or self.lead == user or m.admin

    def notes(self, private=False):
        return self.organizationnote_set.filter(private=private)

    def lock(self):
        self.locked = True
        self.save()

    def set_lead(self, user):
        self.lead = user
        self.save()

    def save_url(self, url_type, url_value):
        if url_type and url_value:
            t = URLType.objects.get(name=url_type)
            self.websites.create(url_type=t, url=url_value)

    def __unicode__(self):
        return self.name

    @property
    def admin_url(self):
        return urlresolvers.reverse('admin:nadine_organization_change', args=[self.id])

    class Meta:
        app_label = 'nadine'
        ordering = ['name']


class OrganizationMember(models.Model):
    """ A record of a user being part of an organization """
    organization = models.ForeignKey(Organization)
    user = models.ForeignKey(User)
    title = models.CharField(max_length=128, null=True, blank=True)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    admin = models.BooleanField(default=False)

    def is_active(self, on_date=None):
        if not on_date:
            on_date = timezone.now().date()
        if self.start_date > on_date:
            return False
        return self.end_date == None or self.end_date >= on_date

    def set_admin(self, is_admin):
        self.admin = is_admin
        self.save()

    @property
    def is_lead(self):
        return self.user == self.organization.lead

    @property
    def is_admin(self):
        return self.admin or self.is_lead

    def __unicode__(self):
        return "%s member of %s" % (self.user, self.organization)


class OrganizationNote(models.Model):
    created_ts = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, related_name="+")
    organization = models.ForeignKey(Organization)
    private = models.BooleanField(default=True)
    note = models.TextField()

    def __str__(self):
        if len(self.note) > 16:
            return "%s: %s" % (self.organization, self.note[16:])
        else:
            return "%s: %s" % (self.organization, self.note)

    class Meta:
        app_label = 'nadine'


class OrganizationMembership(Membership2):
    organization = models.ForeignKey(Organization, related_name="membership")


# Copyright 2017 Office Nomads LLC (http://www.officenomads.com/) Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0 Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
