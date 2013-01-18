{% load imagetags %}
<table class="member-table">
	<tr><th style="text-align:center;">Photo</th><th style="text-align:left;">Name</th><th>Billing Date</th><th>Quicklinks</th></tr>
	{% for member in members %}
	<tr class="{% cycle 'row-even' 'row-odd' %}">
		<td style="text-align:center;">
			{% if member.photo %}<a href="{% url staff.views.member_detail member.id %}"><img class="member-table-photo" src="{{ member.photo.url|fit_image:"48x48"}}" /></a>{% endif %}
		</td>
		<td nowrap style="text-align:left;"><a href="{% url staff.views.member_detail member.id %}">{{ member.first_name }} {{ member.last_name }}</a></td>
		<td>{{ member.last_membership.start_date|date:"M d, Y" }}</td>
		<td style="text-align:center;">	
			<a href="{% url staff.views.member_activity member.id %}">activity</a> |
			<a href="{% url staff.views.member_bills member.id %}">bills </a> |
			<a href="{% url staff.views.member_transactions member.id %}">transactions </a> |
			{% if member.is_active %}
				<a href="{% url staff.views.membership member.last_membership.id %}">membership</a>
			{% else %}	
				<a href="{% url staff.views.member_membership member.id %}">membership</a>
			{% endif %}
		</td>
	</tr>
	{% endfor %}
</table>
