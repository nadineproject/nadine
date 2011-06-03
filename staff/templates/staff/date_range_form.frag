<form class="date-range-form" action="{% if date_range_form_action %}{{ date_range_form_action}}{% else %}.{% endif %}" method="POST">
   From {% for field in date_range_form %} {% ifequal field.name "end" %}to {% endifequal %}{{ field }}{% endfor %} <input type="submit" value="Update">
{% csrf_token %}
</form>
