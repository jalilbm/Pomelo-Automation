# Generated by Django 4.2.4 on 2023-09-12 16:37

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("API", "0005_userlog_type"),
    ]

    operations = [
        migrations.AddField(
            model_name="workgroup",
            name="patient_groups",
            field=models.ManyToManyField(to="API.patientgroup"),
        ),
    ]
