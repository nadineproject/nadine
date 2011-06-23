<div class="columns clearfix">
  <form class="c1" id="member-search-form" action="{% url staff.views.member_search %}" method="post">
  	Find member:
  	{% for field in member_search_form %}{{ field }}{% endfor %}
  	<input type="submit" value="search" />
	{% csrf_token %}
  </form>

  <div class="c2" id="quick-links">
  	Quicklinks:
  	<!--<a href="{% url members.views.index %}">members</a> | -->
  	<a href="{% url staff.views.activity_today %}">record activity</a> |
  	<a href="{% url admin:staff_monthlylog_add %}">add monthly log</a> |
  	<a href="{% url staff.views.signup %}">add member</a>
  </div>  
</div>
