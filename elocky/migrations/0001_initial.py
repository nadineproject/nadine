# Generated by Django 3.0.2 on 2020-01-07 14:28

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ElockyCred',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(max_length=128)),
                ('elocky_id', models. CharField(max_length=128, unique=True)),
                ('num_access', models.CharField(max_length=128)),
                ('code_access', models.CharField(max_length=128)),
            ],
        )
    ]