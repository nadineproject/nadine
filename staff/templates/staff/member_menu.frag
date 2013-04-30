<div id="submenu">
	<a href="{% url "staff.views.signup" %}">add member</a> |
	<a href="{% url "staff.views.activity_today" %}">record activity</a> |
	<a href="{% url "staff.views.security_deposits" %}">security deposits</a> |
	<a href="{% url "staff.views.member_bcc" 0 %}">bcc tool</a> |
	<a href="{% url "staff.views.view_user_reports" %}">user reports</a>
</div>
