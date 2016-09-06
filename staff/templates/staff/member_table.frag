{% load imagetags %}
<table class="member-table">
	<tr>
		<th style="text-align:center;">Photo</th>
		<th style="text-align:left;">Name</th>
		<th>Billing Date</th>
		<th>Quicklinks</th>
		<th>Guests</th>
	</tr>
	{% for m in members %}
		<tr class="{% cycle 'row-even' 'row-odd' %}" >
			<td style="text-align:center;">
				{% if m.photo %}<a href="{% url 'staff_user_detail' m.user.username %}"><img class="member-table-photo" src="{{ m.user.profile.photo.url|fit_image:"48x48"}}" /></a>{% endif %}
			</td>
			<td nowrap style="text-align:left;"><a href="{% url 'staff_user_detail' m.user.username %}">{{ m.user.get_full_name }}</a></td>
			<td>{{ m.last_membership.start_date|date:"M d, Y" }}</td>
			<td style="text-align:center;">
				<a href="{% url 'staff_activity_user' m.user.username %}">activity</a> |
				<a href="{% url 'staff_user_files' m.user.username %}">files</a> |
				<a href="{% url 'staff_user_payment' m.user.username %}">usaepay</a> |
				<a href="{% url 'staff_xero' m.user.username %}">xero</a> |
				{% if m.is_active %}
					<a href="{% url 'staff_membership' m.active_membership.id %}">membership</a>
				{% else %}
					<a href="{% url 'staff_user_membership' m.user.username %}">membership</a>
				{% endif %}
			</td>
			<td style="text-align:center;">
				{% if m.guests %}
					<a href="." onclick="$('#guest-details-{{m.id}}').show(); return false;">{{m.guests|length}}</a>
				{% endif %}
			</td>
		</tr>
		<tr style="display: none;" id="guest-details-{{m.id}}">
			<td colspan="5"><table class="guest-detail" style="margin-left: 5em;">
				{% for guest in m.guests %}
					<tr>
						<td style="border-bottom: 0px solid #ccc;" width="2">{% if guest.photo %}
							<a href="{% url 'staff_user_detail' guest.user.username %}">
								<img class="member-table-photo" src="{{ guest.photo.url|fit_image:"48x48"}}" />
							</a>
						{% endif %}</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">
							<a href="{% url 'staff_user_detail' guest.user.username %}">{{ guest.user.get_full_name }}</a>
						</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">{{ guest.active_membership.membership_plan }}</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">{{ guest.active_membership.start_date }}</td>
					</tr>
				{% endfor %}
			</table></td>
		</tr>
	{% endfor %}
</table>
