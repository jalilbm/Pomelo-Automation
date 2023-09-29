from django.contrib.auth.models import User
from django.db import models


class PomeloCredential(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.EmailField(blank=True, null=True)
    password = models.TextField(blank=True, null=True)
    user_timezone = models.CharField(max_length=50, null=False, blank=False)
    chat_on = models.BooleanField(
        null=True, blank=True, default=False
    )  # Tells if currently the chat is on or off

    def __str__(self):
        return f"{self.user.username} -> {self.email}"


class PatientGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=254, blank=True, null=True)
    added_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class WorkGroup(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=254, blank=True, null=True)
    patient_groups = models.ManyToManyField(PatientGroup)
    added_datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"


class UserLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    type = models.CharField(max_length=16, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.timestamp}"


class Timeframe(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    TYPE_CHOICES = [
        ("Clinic Days", "Clinic Days"),
        ("FHO Clinics", "FHO Clinics"),
        ("STAT Days", "STAT Days"),
        ("Holidays", "Holidays"),
    ]

    TIME_TYPE_CHOICES = [
        ("weekDays", "Week days with specific times"),
        ("dateTimeInterval", "Datetime interval"),
    ]

    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    time_type = models.CharField(max_length=50, choices=TIME_TYPE_CHOICES)
    timezone = models.CharField(max_length=50, null=False, blank=False)
    start_time_day = models.CharField(max_length=50, null=True, blank=True)
    end_time_day = models.CharField(max_length=50, null=True, blank=True)
    from_time = models.TimeField(
        null=True, blank=True
    )  # This will store the time if it's a weekDay type
    to_time = models.TimeField(
        null=True, blank=True
    )  # This will store the time if it's a weekDay type
    from_date = models.DateTimeField(
        null=True, blank=True
    )  # This will store the datetime if it's a dateTimeInterval type
    to_date = models.DateTimeField(
        null=True, blank=True
    )  # This will store the datetime if it's a dateTimeInterval type

    def __str__(self):
        returned_string = f"{self.user.username} - {self.type} | "
        if self.time_type == "weekDays":
            returned_string += (
                f"{self.start_time_day}: {self.from_time} -> {self.to_time}"
            )
        else:
            returned_string += f"{self.from_date} -> {self.to_date}"
        return returned_string
