"""A Django project which provides web applications for coworking spaces."""
from tastypie.api import Api


API = Api(api_name='v1') # The TastyPie API suite used to collect resources from all of the django apps

# This seemingly useless import causes the arpwatch.api module to be evaluated before service begins.
# Inside arpwatch.api each Resource will register itself with nadine.API
from arpwatch.api import ActivityResource

