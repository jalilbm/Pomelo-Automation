# Generated by Django 4.2.4 on 2023-09-24 08:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("API", "0014_remove_patientgroup_chat_on_pomelocredential_chat_on"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="pomelocredential",
            name="password",
        ),
    ]