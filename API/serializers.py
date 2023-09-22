from .models import *
from rest_framework import serializers


class PomeloCredentialSerializer(serializers.ModelSerializer):
    class Meta:
        model = PomeloCredential
        fields = "__all__"


class UserLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLog
        fields = "__all__"


class WorkGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkGroup
        fields = "__all__"


class PatientGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatientGroup
        fields = "__all__"


class TimeframeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timeframe
        fields = "__all__"
