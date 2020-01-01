from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('comlink', '0005_auto_20191231_1511'),
    ]

    operations = [
        # Make received auto_now_add
        migrations.AlterField(
            model_name='emailmessage',
            name='received',
            field=models.DateTimeField(auto_now_add=True, verbose_name='received'),
        ),

        # Remove the old IncomingEmail model
        migrations.RemoveField(
            model_name='attachment',
            name='email',
        ),
        migrations.DeleteModel(
            name='IncomingEmail',
        ),
    ]
