from django.contrib.auth.models import User
from forms import *
from models import Member

REPORT_KEYS = (
	('ALL', 'All Users'),
	('INVALID_BILLING', 'Users with Invalid Billing'),
	('NEW', 'Users with Invalid Billing'),
	('EXITING', 'Users with Invalid Billing'),
)

REPORT_FIELDS = (
	('NAME', 'Name'),
	('START', 'First Visit'),
	('LAST', 'Last Visit'),
)

class User_Report:
	def __init__(self, form):
		self.report = form.data['report']
		self.order_by = form.data['order_by']
		self.active_only = form.data['active_only']

	def get_users(self):
		if self.report == "ALL":
			return self.get_all_users()
		else:
			return None
	
	def get_all_users(self):
		if self.active_only:
			Member.objects.active_members().values('user')
		else:
			return User.objects.all()