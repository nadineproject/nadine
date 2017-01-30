Django Templating
=================

Nadine uses Django as our backend framework. With Django comes the awesome power of the Django templates. The templates are HTML with the Django template language (DTL) and any necessary JavaScript.

For more information on DTL and Django templates, check out `the documentation. <https://docs.djangoproject.com/en/1.10/topics/templates/>`_


Nadine's Usage of Django Templates
----------------------------------

To make the DRY-est html, we have used the templates to manage repeated code. You will notice a base.html in all of the applications. This is the file which will layout the head, navigation, and footer. From there, each of the pages will include a version of:

``{% extends app_name/base.html %}``

In the Staff App, the templates are divided up even more and each of those folders include their own base.html which extends the staff/base.html and then sets some basic navigation styling and brings in a stylesheet for that section.

Below the 'extends' code, there might also be such code as:

``{% load static %}``

This loading of static or settings or whatever is called is bringing in a variable from the backend to be used.

To maintain our DRY code, there are points in the HTML in which the template 'includes' another HTML page. An example of this would be the date_range_form.html which is repeatedly used in the Staff App with:

``{% include "staff/date_range_form.html" %}``

Again, for more info on Django templating, please see `the documentation. <https://docs.djangoproject.com/en/1.10/topics/templates/>`_
