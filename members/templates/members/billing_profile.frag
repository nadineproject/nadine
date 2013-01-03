<div style="margin-left: 2em; margin-bottom: .5em;">
Current Profile: 
{% if member.valid_billing %}
	<font color=green>Valid</font>
{% else %}
	<font color=red>Invalid</font>
{% endif %}
</div>

{% if request.user.is_staff %}
	<div style="margin-left: 2em; margin-bottom: .5em;">
		<form method=POST action="{% url staff.views.toggle_billing_flag member.id %}" onSubmit="return confirm('Are you sure?');">
			<input type="hidden" name="back" value="{{request.get_full_path}}">
			{% if member.valid_billing %}
				<input type="submit" value="Flag Invalid Billing Profile">
			{% else %}
				<input type="submit" value="Clear Invalid Billing Flag">
			{% endif %}
			{% csrf_token %}
		</form>
	</div>
{% endif %}

{% if settings.USA_EPAY_KEY %}
	<div style="margin-left: 2em">
		<form action="https://www.usaepay.com/interface/epayform/">
			<input type="hidden" name="UMkey" value="{{ settings.USA_EPAY_KEY }}">
			<input type="hidden" name="UMdescription" value="Office Nomads Billing Authorization">
			<input type="hidden" name="UMcustid" value="{{ member.user.username }}">
			<input type="hidden" name="UMcommand" value="AuthOnly">
			<input type="hidden" name="UMamount" value="1.00">
			<input type="hidden" name="UMinvoice" value="1617">
			<input type="hidden" name="UMaddcustomer" value="yes">
			<input type="hidden" name="UMschedule" value="disabled">
			<input type="hidden" name="UMsoftware" value="nadine">
			<input type="hidden" name="UMcustreceipt" value="yes">
			<input type="hidden" name="UMname" value="{{ member.full_name }}">
			<input type="hidden" name="UMstreet" value="{{ member.address1 }}">
			<input type="hidden" name="UMzip" value="{{ member.zipcode }}">
			<input type="hidden" name="UMbillfname" value="{{ member.first_name }}">
			<input type="hidden" name="UMbilllname" value="{{ member.last_name }}">
			<input type="hidden" name="UMbillcompany" value="{{ member.company_name }}">
			<!--
			<input type="hidden" name="UMbillstreet" value="{{ member.address1 }}">
			<input type="hidden" name="UMbillstreet2" value="{{ member.address2 }}">
			<input type="hidden" name="UMbillcity" value="{{ member.city }}">
			<input type="hidden" name="UMbillstate" value="{{ member.state }}">
			<input type="hidden" name="UMbillzip" value="{{ member.zipcode }}">
			-->
			<input type="hidden" name="UMbillphone" value="{{ member.phone }}">
			<input type="hidden" name="UMemail" value="{{ member.email }}">
			<!--<input type="hidden" name="UMtestmode" value="true">-->
			<input type="submit" value="Create New Billing Profile">
		</form>
	</div>
{% endif %}

