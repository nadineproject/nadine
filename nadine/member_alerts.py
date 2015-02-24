from nadine.models import Member, MemberAlert, FileUpload

def alert_exists(user, key):
	return MemberAlert.objects.filter(user=user, key=key, resolved_ts__isnull=True, muted_ts__isnull=True).count() > 0

def create_alert(user, key):
	if not alert_exists(user, key):
		MemberAlert.objects.create(user=user, key=key)

def process_active_members():
	for m in Member.objects.active_members():
		trigger_new_membership(m.user)

def trigger_new_membership(user):
	# Pull a bunch of data so we don't keep hitting the database
	open_alerts = user.profile.alerts_by_key(include_resolved=False)
	all_alerts = user.profile.alerts_by_key(include_resolved=True)
	existing_files = user.profile.files_by_type()
	#existing_memberships = user.profile.memberships()
		
	# Member Information
	if not FileUpload.MEMBER_INFO in existing_files:
		if not MemberAlert.PAPERWORK in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.PAPERWORK)
		if not MemberAlert.PAPERWORK in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.MEMBER_INFO)

	# Membership Agreement
	if not FileUpload.MEMBER_AGMT in existing_files:
		if not MemberAlert.MEMBER_AGREEMENT in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.MEMBER_AGREEMENT)
	
	# User Photo
	if not user.profile.photo:
		if not MemberAlert.TAKE_PHOTO in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.TAKE_PHOTO)
		if not MemberAlert.UPLOAD_PHOTO in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.UPLOAD_PHOTO)
	if not MemberAlert.POST_PHOTO in open_alerts:
		MemberAlert.objects.create(user=user, key=MemberAlert.POST_PHOTO)

	# New Member Orientation
	# TODO - Maybe check to see if it's been more then a year?
	if not MemberAlert.ORIENTATION in all_alerts:
		MemberAlert.objects.create(user=user, key=MemberAlert.ORIENTATION)

	# Key?  Check for a key agreement
	last_membership = user.profile.last_membership()
	if last_membership and last_membership.has_key:
		if not FileUpload.KEY_AGMT in existing_files:
			if not MemberAlert.KEY_AGREEMENT in open_alerts:
				MemberAlert.objects.create(user=user, key=MemberAlert.KEY_AGREEMENT)

def trigger_exiting_membership(user):
	open_alerts = user.profile.alerts_by_key(include_resolved=False)
	
	# Take down their photo.  First make sure we have a photo and not an open alert
	if user.profile.photo and not MemberAlert.POST_PHOTO in open_alerts:
		if not MemberAlert.REMOVE_PHOTO in open_alerts:
			MemberAlert.objects.create(user=user, key=MemberAlert.REMOVE_PHOTO)

	# Key?  Let's get it back!
	last_membership = user.profile.last_membership()
	if last_membership:
		if last_membership.has_key:
			if not MemberAlert.RETURN_DOOR_KEY in open_alerts:
				MemberAlert.objects.create(user=user, key=MemberAlert.RETURN_DOOR_KEY)
		if last_membership.has_desk:
			if not MemberAlert.RETURN_DESK_KEY in open_alerts:
				MemberAlert.objects.create(user=user, key=MemberAlert.RETURN_DESK_KEY)

# Class based example to clean up the above implementation
#
# class MemberAlertTriggerException(Exception):
# 	pass
#
# class MemberAlertTrigger(object):
# 	__metaclass__ = ABCMeta
#
# 	__user
# 	__existing_alerts
#
# 	def __init__(self):
# 		pass
#
# 	def __load_existing_alerts():
# 		if not __user:
# 			raise MemberAlertTriggerException("No user")
#
# 		__existing_alerts = {}
# 		for alert in MemberAlert.objects.filter(user=__user, resolved_ts__isnull=True, muted_ts__isnull=True).count():
# 			__existing_alerts[key] = alert
#
# 	@abstractmethod
# 	def get_users(self):
# 		# Return a User QuerySet containing eligible members
# 		pass
#
# class NewMembershipTrigger(MemberAlertTrigger):
# 	pass

# Member Alert Keys
# PAPERWORK = "paperwork"
# MEMBER_INFO = "member_info"
# MEMBER_AGREEMENT = "member_agreement"
# TAKE_PHOTO = "take_photo"
# UPLOAD_PHOTO = "upload_hoto"
# POST_PHOTO = "post_photo"
# ORIENTATION = "orientation"
# KEY_AGREEMENT = "key_agreement"
# STALE_MEMBER = "stale_member"
# INVALID_BILLING = "invalid_billing"
# REMOVE_PHOTO = "remove_photo"
# RETURN_DOOR_KEY = "return_door_key"
# RETURN_DESK_KEY = "return_desk_key"