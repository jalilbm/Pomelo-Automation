# Generated by Django 4.2.4 on 2023-09-18 13:00

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("API", "0008_rename_pomelocredentials_pomelocredential"),
    ]

    operations = [
        migrations.AddField(
            model_name="timeframe",
            name="timezone",
            field=models.CharField(default="Asia/Dubai", max_length=50),
            preserve_default=False,
        ),
    ]
