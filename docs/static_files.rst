Static Files
============

Per Django documentation, Nadine serves static files by setting a STATIC_URL in the settings file and then loading the static shortcut then including it in a path like this:

::

  {% load static %}
  <img src="{% static "img/logo.png" %}" alt="Company Logo"/>

The static folder includes all images Nadine will use, stylesheets, JavaScript files, and fonts. Each application has its own static folder in which you must include any necessary item to be used in that application. 
