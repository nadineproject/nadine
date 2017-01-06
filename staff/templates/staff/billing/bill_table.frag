{% load list_tags %}
<table class="bill-fees">
	<tr>
		<th>Date:</th>
		<td>
			<a href="{% url 'staff:bill' bill.id %}">{{ bill.bill_date|date:"m/d/y" }}</a>
			{% if show_member_name %}for <a href="{% url 'staff:member:detail' bill.user.username %}">{{ bill.user.get_full_name }}</a>{% endif %}
		</td>
	</tr>
	<tr><th>Status:</th>
		<td>
			{% if bill.transactions.all %}
				closed on {% for transaction in bill.transactions.all %}<a href="{% url 'staff:transaction' transaction.id %}">{{ transaction.transaction_date | date:"m/d/y"}}</a>{% endfor %}
			{% else %}
				open
			{% endif %}
		</td>
	</tr>
	<tr><th>Amount:</th> <td>${{ bill.amount }}</td></tr>
	{% if not hide_paid_by %}
		{% if bill.paid_by %}
			<tr>
				<th>Paid by:</th><td><a href="{% url 'staff:member:detail' bill.paid_by.user.username %}">{{ bill.paid_by.user.get_full_name }}</a></td>
			</tr>
		{% endif %}
	{% endif %}
	{% if bill.membership %}
		<tr>
			<th>Monthly:</th>
				<td>
					<a href="{{ bill.membership.get_admin_url }}">{{ bill.membership.membership_plan }} @ ${{ bill.membership.monthly_rate }}</a>:
					started {{ bill.membership.start_date|date:"m/d/y"}}{% if bill.membership.end_date %}, ended {{ bill.membership.end_date|date:"m/d/y"}}{% endif %}
				</td>
		</tr>
		{% if bill.new_member_deposit %}
		<tr>
			<th>Deposit:</th>
			<td>Yes</td>
		</tr>
		{% endif %}
	{% endif %}
	{% if bill.dropins.all %}
	<tr>
		<th>Dropins:</th>
		<td>
			{% for dropin in bill.dropins.all %}
				<a href="{{ dropin.get_admin_url }}">{{ dropin.visit_date|date:"m/d/y" }}</a>{% loop_comma %}
			{% endfor %}
		</td>
	</tr>
	{% endif %}
	{% if bill.guest_dropins.all %}
	<tr>
		<th>Guest Dropins:</th>
		<td>
			{% for dropin in bill.guest_dropins.all %}
				<a href="{% url 'staff:member:detail' dropin.user.username %}">{{dropin.user.get_full_name}}</a>
				on <a href="{{ dropin.get_admin_url }}">{{ dropin.visit_date|date:"m/d/y" }}</a>{% loop_comma %}
			{% endfor %}
		</td>
	</tr>
	{% endif %}
</table>
