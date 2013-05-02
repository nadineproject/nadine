<div id="submenu">
	<a href="{% url 'staff.views.signup' %}">add member</a>  |
	<a href="{% url 'staff.views.activity_today' %}">record activity</a> |
	<a href="{% url 'staff.views.bills' %}">outstanding bills</a> | 
	<a href="{% url 'staff.views.transactions' %}">transactions</a> | 
	<a href="{% url 'staff.views.run_billing' %}">run billing</a>  
</div>