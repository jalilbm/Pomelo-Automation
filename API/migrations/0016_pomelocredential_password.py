# Generated by Django 4.2.4 on 2023-09-24 08:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("API", "0015_remove_pomelocredential_password"),
    ]

    operations = [
        migrations.AddField(
            model_name="pomelocredential",
            name="password",
            field=models.TextField(blank=True, null=True),
        ),
    ]