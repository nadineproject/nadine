from django import forms
from django.contrib.auth.models import User
from datetime import date, datetime, timedelta
from django.utils import timezone
from models import Member, Membership

REPORT_KEYS = (
	('ALL', 'All Users'),
	('NEW_MEMBER', 'New Members'),
	('EXITING_MEMBER', 'Exiting Members'),
	('INVALID_BILLING', 'Users with Invalid Billing'),
)

REPORT_FIELDS = (
	('FIRST', 'First Name'),
	('LAST', 'Last Name'),
	('JOINED', 'Date Joined'),
	#('LAST', 'Last Visit'),
)

def getDefaultForm():
	start = timezone.now().date() - timedelta(days=30)
	end = timezone.now().date()
	form_data = {'report':'ALL', 'order_by':'JOINED', 'active_only':True, 'start_date':start, 'end_date':end}
	return UserReportForm(form_data)

class UserReportForm(forms.Form):
	report = forms.ChoiceField(choices=REPORT_KEYS, required=True)
	order_by = forms.ChoiceField(choices=REPORT_FIELDS, required=True)
	active_only = forms.BooleanField(initial=True)
	start_date = forms.DateField(required=True)
	end_date = forms.DateField(required=True)

class User_Report:
	def __init__(self, form):
		self.report = form.data['report']
		self.order_by = form.data['order_by']
		self.active_only = form.data.has_key('active_only')
		self.start_date = form.data['start_date']
		self.end_date = form.data['end_date']
		if not self.end_date:
			self.end_date = timezone.now().date()
		print(self.end_date)

	def get_users(self):
		# Grab the users we want
		if self.report == "ALL":
			users = self.all_users()
		elif self.report == "NEW_MEMBER":
			users = self.new_membership()
		elif self.report == "EXITING_MEMBER":
			users = self.ended_membership()
		elif self.report == "INVALID_BILLING":
			users = self.invalid_billing()
		if not users:
			return User.objects.none()
		
		# Only active members?
		if self.active_only:
			users = users.filter(pk__in=Member.objects.active_members().values('user'))
		
		# Sort them
		if self.order_by == "FIRST":
			users = users.order_by("first_name")
		elif self.order_by == "LAST":
			users = users.order_by("last_name")
		elif self.order_by == "JOINED":
			users = users.order_by("date_joined")
	
		# Done!
		return users
	
	def all_users(self):
		return User.objects.filter(date_joined__gte=self.start_date, date_joined__lte=self.end_date)

	def new_membership(self):
		new_memberships = Membership.objects.filter(start_date__gte=self.start_date, start_date__lte=self.end_date)
		members = Member.objects.filter(memberships__in=new_memberships)
		return User.objects.filter(pk__in=members.values('user'))

	def ended_membership(self):
		ended_memberships = Membership.objects.filter(end_date__gte=self.start_date, end_date__lte=self.end_date)
		members = Member.objects.filter(memberships__in=ended_memberships)
		return User.objects.filter(pk__in=members.values('user'))

	def invalid_billing(self):
		members = Member.objects.filter(valid_billing=False)
		return User.objects.filter(pk__in=members.values('user'), date_joined__gte=self.start_date, date_joined__lte=self.end_date)
		