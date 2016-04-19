<div id="submenu">
	<a href="{% url 'staff.views.activity.for_today' %}">record activity</a> |
	<a href="{% url 'staff.views.billing.bills' %}">outstanding bills</a> |
	<a href="{% url 'staff.views.payment.usaepay_transactions_today' %}">daily charges</a> |
	<a href="{% url 'staff.views.payment.usaepay_members' %}">auto-billing</a> |
	<a href="{% url 'staff.views.billing.run_billing' %}">run billing</a>  
</div>
