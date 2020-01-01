from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('comlink', '0005_Import_Interlink'),
    ]

    operations = [
        # Make received auto_now_add
        migrations.AlterField(
            model_name='emailmessage',
            name='received',
            field=models.DateTimeField(auto_now_add=True, verbose_name='received'),
        ),

        # Clean up the old IncomingEmail model
        migrations.RemoveField(
            model_name='attachment',
            name='email',
        ),
        migrations.DeleteModel(
            name='IncomingEmail',
        ),

    ]
