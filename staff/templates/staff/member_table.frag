{% load imagetags %}
<table class="member-table">
	<tr><th>Name</th><th>First visit</th><th>Duration</th><th>Photo</th></tr>
	{% for member in members %}
	<tr class="{% cycle 'row-even' 'row-odd' %}">
		<td><a href="{% url staff.views.member_detail member.id %}">{{ member.first_name }} {{ member.last_name }}</a></td>
		<td><a href="{% url staff.views.member_activity member.id %}">{{ member.first_visit|date:"M y" }}</a></td>
		<td>{{ member.first_visit|timesince }}</td>
		<td>
			{% if member.photo %}<a href="{% url staff.views.member_detail member.id %}"><img class="member-table-photo" src="{{ member.photo.url|fit_image:"48x48"}}" /></a>{% endif %}
		</td>
	</tr>
	{% endfor %}
</table>
