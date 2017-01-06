<div id="submenu">
	<a href="{% url 'staff:activity:today' %}">record activity</a> |
	<a href="{% url 'staff:billing:bills' %}">outstanding bills</a> |
	<a href="{% url 'staff:billing:charges_today' %}">daily charges</a> |
	<a href="{% url 'staff:billing:payments_members' %}">auto-billing</a> |
	<a href="{% url 'staff:billing:run' %}">run billing</a>
</div>
