{% load imagetags %}
{% load list_tags %}

<div class="user-card">
      {% if member.photo %}
         <a class="photo" href="{% url 'members.views.user' member.user.username %}"><img src="{{ member.photo.url|fit_image:"170x170" }}" /></a>
      {% else %}
         <a class="photo" href="{% url 'members.views.user' member.user.username %}">&#9733;</a>
      {% endif %}         
      <a href="{% url 'members.views.user' member.user.username %}">{{ member.full_name }}</a>
</div>
