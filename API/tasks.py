from __future__ import absolute_import, unicode_literals

from datetime import datetime, time, timedelta
from celery import shared_task
from .utils import PomeloTasks, add_log
from .models import *
import pytz


weekday_mapping = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}


def get_next_weekday_datetime(weekday_str, check_time):
    """
    Get the next datetime for a specific time on a given weekday.
    """

    # Convert the weekday string to its integer value
    weekday = weekday_mapping.get(weekday_str)
    if weekday is None:
        raise ValueError(f"Invalid weekday string: {weekday_str}")

    # Get today's date
    utc_now = datetime.now(pytz.utc)
    today = utc_now.date()

    # Find the next specified weekday from today
    days_ahead = weekday - today.weekday()
    if days_ahead < 0:  # Target day already happened this week
        days_ahead += 7
    elif days_ahead == 0:  # Target day is today
        current_time = utc_now.time()
        # Extract hours and minutes from check_time and current_time
        check_time_hours_minutes = (check_time.hour, check_time.minute)
        current_time_hours_minutes = (current_time.hour, current_time.minute)

        if check_time_hours_minutes < current_time_hours_minutes:
            # The event time has already passed for today
            days_ahead += 7

    target_date = today + timedelta(days_ahead)
    return datetime.combine(target_date, check_time).replace(tzinfo=pytz.utc)


def is_time_on_weekday_between_two_datetimes(
    weekday_str, check_time, from_date, to_date
):
    """
    Check if a specific time on a given weekday
    ("Monday", "Tuesday", ..., "Sunday") falls within between two datetimes.
    """

    target_datetime = get_next_weekday_datetime(weekday_str, check_time)

    # Ensure from_date and to_date are timezone-aware
    if from_date.tzinfo is None:
        from_date = from_date.replace(tzinfo=pytz.utc)
    if to_date.tzinfo is None:
        to_date = to_date.replace(tzinfo=pytz.utc)

    # Check if the target time on the target day is within the holiday interval
    return from_date <= target_datetime < to_date


def timeframe_from_weekday_and_time_not_in_holidays_or_stat_days(timeframe, user):
    # checks a week day from_time
    stat_days_timeframes = Timeframe.objects.filter(user=user, type="STAT Days")
    for stat_timeframe in stat_days_timeframes:
        if is_time_on_weekday_between_two_datetimes(
            timeframe.start_time_day,
            timeframe.from_time,
            stat_timeframe.from_date,
            stat_timeframe.to_date,
        ):
            return False

    holidays_timeframes = Timeframe.objects.filter(user=user, type="Holidays")
    return not any(
        is_time_on_weekday_between_two_datetimes(
            timeframe.start_time_day,
            timeframe.from_time,
            holiday_timeframe.from_date,
            holiday_timeframe.to_date,
        )
        for holiday_timeframe in holidays_timeframes
    )


def timeframe_to_weekday_and_time_not_in_holidays_or_stat_days(timeframe, user):
    # checks a week day to_time
    stat_days_timeframes = Timeframe.objects.filter(user=user, type="STAT Days")
    for stat_timeframe in stat_days_timeframes:
        if is_time_on_weekday_between_two_datetimes(
            timeframe.end_time_day,
            timeframe.to_time,
            stat_timeframe.from_date,
            stat_timeframe.to_date,
        ):
            return False

    holidays_timeframes = Timeframe.objects.filter(user=user, type="Holidays")
    return not any(
        is_time_on_weekday_between_two_datetimes(
            timeframe.end_time_day,
            timeframe.to_time,
            holiday_timeframe.from_date,
            holiday_timeframe.to_date,
        )
        for holiday_timeframe in holidays_timeframes
    )


def end_time_not_fho(timeframe, user):
    timeframe_end_date_time = get_next_weekday_datetime(
        timeframe.end_time_day, timeframe.to_time
    )
    exists = Timeframe.objects.filter(
        user=user,
        type="FHO Clinics",
        end_datetime=timeframe_end_date_time,
    ).exists()

    return not exists


def datetime_not_between_two_datetimes(target_datetime, start_datetime, end_datetime):
    """
    Check if target_datetime is between start_datetime and end_datetime.

    Args:
    - target_datetime (datetime): The datetime to check.
    - start_datetime (datetime): The start of the interval.
    - end_datetime (datetime): The end of the interval.

    Returns:
    - bool: True if target_datetime is between start_datetime and end_datetime, False otherwise.
    """
    return start_datetime <= target_datetime < end_datetime


def timeframe_from_datetime_not_in_holidays(timeframe: Timeframe, user):
    return not any(
        datetime_not_between_two_datetimes(
            timeframe.from_date,
            holiday_timeframe.from_date,
            holiday_timeframe.to_date,
        )
        for holiday_timeframe in Timeframe.objects.filter(user=user, type="Holidays")
    )


def timeframe_from_datetime_not_in_holidays_and_stat_days(timeframe: Timeframe, user):
    in_holidays = any(
        datetime_not_between_two_datetimes(
            timeframe.from_date,
            holiday_timeframe.from_date,
            holiday_timeframe.to_date,
        )
        for holiday_timeframe in Timeframe.objects.filter(user=user, type="Holidays")
    )
    if in_holidays:
        return False
    in_stat_days = in_holidays = any(
        datetime_not_between_two_datetimes(
            timeframe.from_date,
            stat_day_timeframe.from_date,
            stat_day_timeframe.to_date,
        )
        for stat_day_timeframe in Timeframe.objects.filter(user=user, type="STAT Days")
    )
    if in_stat_days:
        return False
    return True


def turn_messages_on(user, timeframe):
    add_log(user, f"Turning {timeframe.type} messages ON...")
    PomeloTasks(user).turn_messages_on()
    PomeloCredential.objects.filter(user=user).update(chat_on=True)
    add_log(user, f"Turned {timeframe.type} messages ON", type="success")


def turn_messages_off(user, timeframe):
    add_log(user, f"Turning {timeframe.type} messages OFF...")
    PomeloTasks(user).turn_messages_off()
    PomeloCredential.objects.filter(user=user).update(chat_on=False)
    add_log(user, f"Turned {timeframe.type} messages OFF", type="success")


@shared_task(queue="handle_messages_activation_queue")
def handle_messages_activation(timeframe_id, messages_on, user_id):
    timeframe = Timeframe.objects.get(pk=timeframe_id)
    user = User.objects.get(pk=user_id)
    user_messages_on = PomeloCredential.objects.get(user=user).chat_on
    print(
        "timeframe",
        timeframe,
        "messages_on",
        messages_on,
        "user_id",
        user_id,
        "timeframe.chat_on",
        user_messages_on,
        "timeframe.type",
        timeframe.type,
    )
    # Check Clinic Days
    if timeframe.type.lower() == "clinic days":
        if messages_on:
            # if the timeframe is for turning messages ON
            # if user_messages_on:
            #     # Chat already ON
            #     return
            # if the timeframe is for turning messages ON
            if timeframe_from_weekday_and_time_not_in_holidays_or_stat_days(
                timeframe, user
            ):
                turn_messages_on(user, timeframe)
                return
            return
        else:
            # if the timeframe is for turning messages OFF
            if (
                # user_messages_on
                # and
                end_time_not_fho(timeframe, user)
                and timeframe_to_weekday_and_time_not_in_holidays_or_stat_days(
                    timeframe, user
                )
            ):
                # Chat is ON and not in an FHO
                turn_messages_off(user, timeframe)
                return
    elif timeframe.type.lower() == "fho clinics":
        if messages_on:
            # if the timeframe is for turning messages ON
            # if user_messages_on:
            #     # Chat already ON
            #     return
            if timeframe_from_datetime_not_in_holidays_and_stat_days(timeframe, user):
                turn_messages_on(user, timeframe)
                return
            return
        else:
            # if the timeframe is for turning messages OFF
            if (
                # user_messages_on
                # and
                timeframe_from_datetime_not_in_holidays_and_stat_days(timeframe, user)
            ):
                # Chat is ON
                turn_messages_off(user, timeframe)
                return
    elif timeframe.type.lower() == "stat days":
        # STAT days are not responsible of turning messages on
        if (
            not messages_on
            # and user_messages_on
            and timeframe_from_datetime_not_in_holidays(timeframe, user)
        ):
            turn_messages_off(user, timeframe)
            return
        elif messages_on:
            timeframe.delete()
    elif timeframe.type.lower() == "holidays":
        # Holidays are not responsible of turning messages on
        # if not messages_on and user_messages_on:
        if not messages_on:
            turn_messages_off(user, timeframe)
            return
        elif messages_on:
            timeframe.delete()
