from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from .models import *
from .serializers import *
from django.contrib.auth.hashers import make_password
from rest_framework import viewsets
from .utils import *
import traceback


class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        user = authenticate(
            request,
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        return super().post(request, *args, **kwargs)


class SettingsView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        data = request.data
        print(data)

        # If the request contains the "password" field, update the user's password
        if "password" in data:
            request.user.password = make_password(data["password"])
            request.user.save()

        # Try to get the PomeloCredential object for the user or create a new one if it doesn't exist
        pomelo_object, created = PomeloCredential.objects.get_or_create(
            user=request.user
        )

        # Update the email and password fields
        pomelo_object.email = data.get("pomeloEmail")
        pomelo_object.password = data.get("pomeloPassword")
        pomelo_object.save()

        return Response(
            {"message": "Settings saved successfully."}, status=status.HTTP_201_CREATED
        )

    def get(self, request):
        try:
            pomelo_credentials = PomeloCredential.objects.get(user=request.user)
            serializer = PomeloCredentialSerializer(pomelo_credentials)
        except Exception:
            serializer = None
        return Response(
            serializer.data if serializer else {"email": None, "password": None},
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data["refresh_token"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST)


class UserLogViewSet(viewsets.ModelViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserLogSerializer

    def get_queryset(self):
        # Filter logs by the authenticated user
        return UserLog.objects.filter(user=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        if not queryset.exists():
            return Response([], status=status.HTTP_200_OK)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WorkGroupsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            work_groups = WorkGroup.objects.filter(user=request.user)
            serializer = WorkGroupSerializer(work_groups, many=True)
            work_groups_data = serializer.data
        except Exception:
            print(traceback.format_exc())
            work_groups_data = []
        try:
            patient_groups = PatientGroup.objects.filter(user=request.user)
            serializer = PatientGroupSerializer(patient_groups, many=True)
            patient_groups_data = serializer.data
        except Exception:
            print(traceback.format_exc())
            patient_groups_data = []
        return Response(
            {"work_groups": work_groups_data, "patient_groups": patient_groups_data},
            status=status.HTTP_200_OK,
        )

    def put(self, request):
        if result := PomeloTasks(request.user).update_work_groups():
            return Response(result, status=status.HTTP_200_OK)
        else:
            return Response(
                {
                    "error": "Operation Failed: Check your Pomelo credentials or try again in few minutes"
                },
                status=status.HTTP_200_OK,
            )

    def post(self, request):
        data = request.data
        user = request.user
        for group_data in data:
            work_group = WorkGroup.objects.get(user=user, title=group_data["title"])
            patient_groups = PatientGroup.objects.filter(
                id__in=group_data["patient_groups"]
            )
            work_group.patient_groups.set(patient_groups)
            add_log(
                user, f"Updated patient groups for {work_group.title}", type="success"
            )
        return Response({"message": "Successfully updated work groups"}, status=200)


class TimeframeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        timeframes = Timeframe.objects.filter(user=request.user)
        serializer = TimeframeSerializer(timeframes, many=True)
        data = serializer.data
        for i, d in enumerate(data):
            if d.get("time_type") == "weekDays":
                day_to_send = get_day_to_send(
                    d.get("from_time"), d.get("timezone"), d.get("start_time_day")
                )
                data[i]["day"] = day_to_send
        return Response(data, status=status.HTTP_200_OK)

    def get_object(self, pk, user):
        try:
            return Timeframe.objects.get(pk=pk, user=user)
        except Timeframe.DoesNotExist:
            return None

    def post(self, request):
        timeframes_data = request.data
        print(timeframes_data)

        # Step 1: Fetch all existing timeframes for the user
        existing_timeframes = Timeframe.objects.filter(user=request.user)
        existing_ids = {tf.id for tf in existing_timeframes}
        processed_ids = set()
        user_timezone = timeframes_data.pop("timezone")

        for key, timeframes in timeframes_data.items():
            for timeframe_data in timeframes:
                # Add the type, time_type, and user fields based on the data structure
                timeframe_data["type"] = key
                if timeframe_data.get("day") is None or timeframe_data["day"] is None:
                    timeframe_data["time_type"] = "dateTimeInterval"
                    timeframe_data["from_date"] = timeframe_data["fromDate"]
                    timeframe_data["to_date"] = timeframe_data["toDate"]
                    timeframe_data["timezone"] = user_timezone
                else:
                    timeframe_data["time_type"] = "weekDays"
                    timeframe_data["timezone"] = user_timezone
                    user_day = timeframe_data["day"]
                    timeframe_data["start_time_day"] = get_day_to_store(
                        timeframe_data["from"], user_timezone, user_day
                    )
                    timeframe_data["end_time_day"] = get_day_to_store(
                        timeframe_data["to"], user_timezone, user_day
                    )
                    timeframe_data["from_time"] = timeframe_data["from"]
                    timeframe_data["to_time"] = timeframe_data["to"]
                timeframe_data["user"] = request.user.id

                if "id" in timeframe_data:
                    # Update existing timeframe
                    try:
                        timeframe = Timeframe.objects.get(
                            id=timeframe_data["id"], user=request.user
                        )
                        if timeframe.user != request.user:
                            return Response(
                                {"error": "Unauthorized access"},
                                status=status.HTTP_403_FORBIDDEN,
                            )
                        serializer = TimeframeSerializer(timeframe, data=timeframe_data)
                        if not serializer.is_valid():
                            add_log(
                                request.user,
                                f"[Timeframe Update Error] {str(serializer.errors)}",
                                type="error",
                            )
                            return Response(
                                serializer.errors, status=status.HTTP_400_BAD_REQUEST
                            )
                        serializer.save()
                        processed_ids.add(timeframe_data["id"])
                        add_log(
                            request.user,
                            f"Updated {timeframe_data['time_type']} timeframe",
                            type="success",
                        )
                    except Timeframe.DoesNotExist:
                        return Response(
                            {"error": "Timeframe not found"},
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    # Create new timeframe
                    serializer = TimeframeSerializer(data=timeframe_data)
                    if serializer.is_valid():
                        saved_timeframe = serializer.save(user=request.user)
                        processed_ids.add(saved_timeframe.id)
                        add_log(
                            request.user,
                            f"Added new {timeframe_data['time_type']} timeframe",
                            type="success",
                        )
                    else:
                        print(serializer.errors)
                        add_log(
                            request.user,
                            f"[Add Timeframe Error] {str(serializer.errors)}",
                            type="error",
                        )
                        return Response(
                            serializer.errors, status=status.HTTP_400_BAD_REQUEST
                        )

        # Step 3: Delete any existing timeframe not in the processed list
        ids_to_delete = existing_ids - processed_ids
        if len(ids_to_delete) > 0:
            # First, delete the Timeframe objects
            Timeframe.objects.filter(id__in=ids_to_delete).delete()
            add_log(
                request.user,
                f"[Deleted] {len(ids_to_delete)} timeframes",
                type="success",
            )

        # Now, go through the entire Timeframe table and identify tasks that should exist
        valid_ids = set(Timeframe.objects.values_list("id", flat=True))

        # Identify PeriodicTasks that are associated with the valid Timeframe IDs
        task_names_to_keep = []
        for task_name in PeriodicTask.objects.values_list("name", flat=True):
            if "ID " in task_name:
                # Extract the ID from the task name
                task_id = int(task_name.split("ID ")[-1])
                if task_id in valid_ids:
                    task_names_to_keep.append(task_name)

        # Delete the PeriodicTasks that are not in the task_names_to_keep list
        PeriodicTask.objects.exclude(name__in=task_names_to_keep).delete()

        # Clean up any CrontabSchedule objects that are no longer associated with any PeriodicTask
        used_crontabs = PeriodicTask.objects.values_list("crontab", flat=True)
        CrontabSchedule.objects.exclude(id__in=used_crontabs).delete()

        # Clean up any IntervalSchedule objects that are no longer associated with any PeriodicTask
        used_intervals = PeriodicTask.objects.values_list("interval", flat=True)
        IntervalSchedule.objects.exclude(id__in=used_intervals).delete()

        schedule_tasks()
        return Response(
            {"message": "Data processed successfully"}, status=status.HTTP_201_CREATED
        )

    def put(self, request, pk):
        timeframe = self.get_object(pk, request.user)
        if not timeframe:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = TimeframeSerializer(timeframe, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        timeframe = self.get_object(pk, request.user)
        if not timeframe:
            return Response(status=status.HTTP_404_NOT_FOUND)

        timeframe.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
