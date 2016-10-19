from django.core.management.base import NoArgsCommand, CommandError
from django.core.files import File
from django.contrib.auth.models import User

class Command(NoArgsCommand):
    help = "Create an admin user."
    requires_system_checks = True

    def handle_noargs(self, **options):
        if not User.objects.filter(username="admin"):
            print("Creating admin user with username='admin' and password='admin'")
            User.objects.create_superuser('admin', 'admin@example.com', 'admin')
        else:
            print("Admin user already exists!")
