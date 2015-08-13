{% load imagetags %}
<table class="member-table">
	<tr>
		<th style="text-align:center;">Photo</th>
		<th style="text-align:left;">Name</th>
		<th>Billing Date</th>
		<th>Quicklinks</th>
		<th>Guests</th>
	</tr>
	{% for member in members %}
		<tr class="{% cycle 'row-even' 'row-odd' %}" >
			<td style="text-align:center;">
				{% if member.photo %}<a href="{% url 'staff.views.member_detail' member.id %}"><img class="member-table-photo" src="{{ member.photo.url|fit_image:"48x48"}}" /></a>{% endif %}
			</td>
			<td nowrap style="text-align:left;"><a href="{% url 'staff.views.member_detail' member.id %}">{{ member.first_name }} {{ member.last_name }}</a></td>
			<td>{{ member.last_membership.start_date|date:"M d, Y" }}</td>
			<td style="text-align:center;">	
				<a href="{% url 'staff.views.member_activity' member.id %}">activity</a> |
				<a href="{% url 'staff.views.member_files' member.id %}">files</a> |
				<a href="{% url 'staff.views.usaepay_user' member.user.username %}">usaepay</a> |
				<a href="{% url 'staff.views.xero_user' member.user.username %}">xero</a> |
				{% if member.is_active %}
					<a href="{% url 'staff.views.membership' member.active_membership.id %}">membership</a>
				{% else %}	
					<a href="{% url 'staff.views.member_membership' member.id %}">membership</a>
				{% endif %}
			</td>
			<td style="text-align:center;">
				{% if member.guests %}
					<a href="." onclick="$('#guest-details-{{member.id}}').show(); return false;">{{member.guests|length}}</a>
				{% endif %}
			</td>
		</tr>
		<tr style="display: none;" id="guest-details-{{member.id}}">
			<td colspan="5"><table class="guest-detail" style="margin-left: 5em;">
				{% for guest in member.guests %}
					<tr>
						<td style="border-bottom: 0px solid #ccc;" width="2">{% if guest.photo %}
							<a href="{% url 'staff.views.member_detail' guest.id %}">
								<img class="member-table-photo" src="{{ guest.photo.url|fit_image:"48x48"}}" />
							</a>
						{% endif %}</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">
							<a href="{% url 'staff.views.member_detail' guest.id %}">{{ guest.first_name }} {{ guest.last_name }}</a>
						</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">{{ guest.active_membership.membership_plan }}</td>
						<td style="text-align: left; border-bottom: 0px solid #ccc; padding: 0.5em;">{{ guest.active_membership.start_date }}</td>
					</tr>
				{% endfor %}
			</table></td>
		</tr>
	{% endfor %}
</table>