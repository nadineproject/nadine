<div id="submenu">
	<a href="{% url 'staff.views.activity_today' %}">record activity</a> |
	<a href="{% url 'staff.views.bills' %}">outstanding bills</a> | 
	<a href="{% url 'staff.views.usaepay_transactions_today' %}">daily charges</a> | 
	<a href="{% url 'staff.views.usaepay_members' %}">auto-billing</a> | 
	<a href="{% url 'staff.views.run_billing' %}">run billing</a>  
</div>