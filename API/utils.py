import contextlib
import time
from .models import *
import undetected_chromedriver as uc
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import pytz
from datetime import datetime, date, timedelta
import traceback
from django_celery_beat.models import PeriodicTask, CrontabSchedule, IntervalSchedule
import json
from decouple import config
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from cryptography.fernet import Fernet
from base64 import urlsafe_b64encode
from django.db.models import Q


CHROMEDRIVER_PATH = config("CHROMEDRIVER_PATH")
CHROME_PATH = config("CHROME_PATH")

week_days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

day_mapping = {
    "Monday": "1",
    "Tuesday": "2",
    "Wednesday": "3",
    "Thursday": "4",
    "Friday": "5",
    "Saturday": "6",
    "Sunday": "7",
}

# Convert Django's SECRET_KEY to a suitable format
key = urlsafe_b64encode(config("SECRET_KEY").encode()[:32])


def get_fernet_cipher():
    cipher_suite = Fernet(key)
    return cipher_suite


def encrypt_password(password: str) -> str:
    cipher_suite = get_fernet_cipher()
    encrypted_text = cipher_suite.encrypt(password.encode())
    return encrypted_text.decode()


def decrypt_password(encrypted_password: str) -> str:
    cipher_suite = get_fernet_cipher()
    decrypted_text = cipher_suite.decrypt(encrypted_password.encode())
    return decrypted_text.decode()


def get_driver():
    service = Service(executable_path=CHROMEDRIVER_PATH)
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def add_log(user, content, type="info"):
    UserLog.objects.create(user=user, content=content, type=type)


class PomeloTasks:
    def __init__(self, user):
        self.driver = get_driver()
        self.user = user

    def restart_driver(self):
        self.driver.quit()
        self.driver = get_driver()

    def click_element_by_text(self, text):
        element = self.driver.find_element(By.XPATH, f"//strong[text()='{text}']")
        element.click()

    def login(self):
        credentials = PomeloCredential.objects.get(user=self.user)
        decrypted_password = decrypt_password(credentials.password)
        # Try 3 times to login
        for _ in range(3):
            with contextlib.suppress(TimeoutException):
                add_log(self.user, f"Login attempt {_ + 1}")
                # Get login page
                self.driver.get("https://portal.healthmyself.net/login/#/")
                # Wait for email input
                email_input = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.ID, "email"))
                )
                # Enter email and password
                email_input.send_keys(credentials.email)
                password_input = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[name="password"]')
                    )
                )
                password_input.send_keys(decrypted_password)
                # Click login button
                login_button = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-cy="submit-button"]')
                    )
                )
                login_button.click()
                return bool(
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located(
                            (By.CSS_SELECTOR, ".board-inner")
                        )
                    )
                )
        return False

    def update_work_groups(self):
        add_log(self.user, "Updating work group")
        if self.login():
            add_log(self.user, "Logged in successfully", type="success")
            pomelo_work_groups = self.get_pomelo_work_groups()
            pomelo_patient_groups = self.get_pomelo_patient_groups()
            self.driver.quit()
            return {
                "work_groups": pomelo_work_groups,
                "patient_groups": pomelo_patient_groups,
            }
        else:
            self.driver.quit()
            add_log(
                self.user,
                "Can't Log In: Check your Pomelo credentials or try again in few minutes",
                type="error",
            )
            return False

    def get_pomelo_work_groups(self):
        add_log(self.user, "Getting work groups...")
        self.driver.get(
            "https://portal.healthmyself.net/myfamilymd/portal/settings#/workgroups"
        )
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[class="list-group"]'))
        )

        # Find all the name elements
        name_elements = self.driver.find_elements(
            By.CSS_SELECTOR, ".list-group .name > strong"
        )
        titles = [name_element.text.strip() for name_element in name_elements]

        for title in titles:
            # This will get the object if it exists, or create it if it doesn't
            WorkGroup.objects.get_or_create(user=self.user, title=title)

        # Delete WorkGroup objects for the user if the title is not in titles
        WorkGroup.objects.filter(user=self.user).exclude(title__in=titles).delete()

        add_log(self.user, "Successfully got work groups", type="success")
        return titles

    def get_pomelo_patient_groups(self):
        add_log(self.user, "Getting patient groups...")
        self.driver.get(
            "https://portal.healthmyself.net/myfamilymd/portal/settings#/patient-groups"
        )
        WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[class="list-group"]'))
        )

        # Find all the name elements
        name_elements = self.driver.find_elements(By.CSS_SELECTOR, ".list-group .name")
        titles = [name_element.text.strip() for name_element in name_elements]

        for title in titles:
            # This will get the object if it exists, or create it if it doesn't
            PatientGroup.objects.get_or_create(user=self.user, title=title)

        # Delete PatientGroup objects for the user if the title is not in titles
        PatientGroup.objects.filter(user=self.user).exclude(title__in=titles).delete()

        add_log(self.user, "Successfully got patient groups", type="success")
        return titles

    def navigate_to_work_group(self, work_group_title):
        self.driver.get(
            "https://portal.healthmyself.net/myfamilymd/portal/settings#/workgroups"
        )
        # work groups page
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//strong[text()='{work_group_title}']")
            )
        )
        element.click()
        # settings page
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//h2[contains(text(), 'General Settings')]")
            )
        )
        element.click()

    def click_reset(self):
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "(//div[@class='form-group'])[1]//i[@class='fa fa-square-o']",
                )
            )
        )
        time.sleep(2)
        element.click()

    def select_patient_groups(self, work_group):
        patient_groups = work_group.patient_groups.all()
        # click right patient groups list button
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    "(//div[@class='form-group'])[1]//div[@class='right']//button[@class='btn btn-default btn-sm']",
                )
            )
        )
        element.click()
        for p in patient_groups:
            # click checkboxes
            element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        f"(//div[@class='form-group'])[1]//label[@class='checkbox checkbox-default full'][.//*[text()='{p.title}']]",
                    )
                )
            )
            element.click()

    def click_save(self):
        element = WebDriverWait(self.driver, 30).until(
            EC.presence_of_element_located(
                (By.XPATH, "//button[.//span[contains(text(), 'Save')]]")
            )
        )
        element.click()

    def turn_messages_on(self):
        add_log(self.user, "Turning messages ON...")
        if self.login():
            add_log(self.user, "Logged in successfully", type="success")
            work_groups = WorkGroup.objects.filter(user=self.user)
            for w_g in work_groups:
                add_log(self.user, f"Turning ON messages for {w_g.title}")
                self.navigate_to_work_group(w_g.title)
                self.click_reset()
                self.select_patient_groups(w_g)
                time.sleep(1)
                self.click_save()
                time.sleep(5)
            self.driver.quit()
            add_log(
                self.user,
                "Turned ON all work group messages successfully",
                type="success",
            )
            return True
        else:
            self.driver.quit()
            add_log(
                self.user,
                "Can't Log In: Check your Pomelo credentials or try again in few minutes",
                type="error",
            )
            return False

    def turn_messages_off(self):
        add_log(self.user, "Turning messages OFF...")
        if self.login():
            add_log(self.user, "Logged in successfully", type="success")
            work_groups = WorkGroup.objects.filter(user=self.user)
            for w_g in work_groups:
                add_log(self.user, f"Turning OFF messages for {w_g.title}")
                self.navigate_to_work_group(w_g.title)
                self.click_reset()
                time.sleep(1)
                self.click_save()
                time.sleep(5)
            self.driver.quit()
            add_log(
                self.user,
                "Turned OFF all work group messages successfully",
                type="success",
            )
            return True
        else:
            self.driver.quit()
            add_log(
                self.user,
                "Can't Log In: Check your Pomelo credentials or try again in few minutes",
                type="error",
            )
            return False


def is_task_for_turning_chat_on(timeframe_type, is_from_time):
    if timeframe_type.lower() == "clinic days":
        return is_from_time
    elif timeframe_type.lower() == "fho clinics":
        return is_from_time
    elif timeframe_type.lower() == "stat days":
        return not is_from_time
    elif timeframe_type.lower() == "holidays":
        return not is_from_time


def schedule_tasks():
    for timeframe in Timeframe.objects.all():
        # Helper function to create or update tasks
        def create_or_update_task(day, hour, minute, task_type, timeframe_type):
            # Create a filter to find tasks with the same username, timeframe_type, and day
            existing_tasks = PeriodicTask.objects.filter(
                Q(name__icontains=f"for {timeframe.user.username} on")
                & Q(name__contains=timeframe_type),
                crontab__day_of_week=str(day),
            )
            # If a task exists, update it
            if existing_tasks.exists():
                task = existing_tasks.first()
                task.crontab.day_of_week = str(day)
                task.crontab.hour = hour
                task.crontab.minute = minute
                task.crontab.save()
                task.save()
            else:
                # Otherwise, create a new task
                task_name = f"{task_type} for {timeframe.user.username} on {day} ({timeframe_type}) - ID {timeframe.id}"
                schedule, _ = CrontabSchedule.objects.get_or_create(
                    day_of_week=str(day),
                    hour=hour,
                    minute=minute,
                )
                PeriodicTask.objects.create(
                    name=task_name,
                    task="API.tasks.handle_messages_activation",
                    crontab=schedule,
                    args=json.dumps(
                        [
                            timeframe.id,
                            is_task_for_turning_chat_on(
                                timeframe_type, task_type == "Start Time"
                            ),
                            timeframe.user.id,
                        ]
                    ),
                    queue="handle_messages_activation_queue",
                )

        if timeframe.time_type == "weekDays":
            # Schedule tasks for start and end times
            create_or_update_task(
                day_mapping[timeframe.start_time_day],
                timeframe.from_time.hour,
                timeframe.from_time.minute,
                "Start Time",
                timeframe.type,
            )
            create_or_update_task(
                day_mapping[timeframe.end_time_day],
                timeframe.to_time.hour,
                timeframe.to_time.minute,
                "End Time",
                timeframe.type,
            )

        elif timeframe.time_type == "dateTimeInterval":
            # Helper function to create or update one-off tasks
            def create_or_update_one_off_task(date_time, task_type, timeframe_type):
                task_name = f"{task_type} for {timeframe.user.username} on {date_time.strftime('%Y-%m-%d %H:%M')} ({timeframe_type}) - ID {timeframe.id}"
                try:
                    task = PeriodicTask.objects.get(name=task_name)
                    task.interval.every = (
                        99999  # A large number of days to make it effectively one-off
                    )
                    task.interval.save()
                    task.save()
                except PeriodicTask.DoesNotExist:
                    # Create a very long interval to make it effectively a one-off task
                    interval, _ = IntervalSchedule.objects.get_or_create(
                        every=9999, period="days"
                    )
                    PeriodicTask.objects.create(
                        name=task_name,
                        task="API.tasks.handle_messages_activation",
                        interval=interval,
                        start_time=date_time,
                        args=json.dumps(
                            [
                                timeframe.id,
                                is_task_for_turning_chat_on(
                                    timeframe_type, task_type == "Start Date"
                                ),
                                timeframe.user.id,
                            ]
                        ),  # or False depending on your logic
                        queue="handle_messages_activation_queue",  # Add this line
                    )

            # Schedule tasks for start and end dates
            create_or_update_one_off_task(
                timeframe.from_date, "Start Date", timeframe.type
            )
            create_or_update_one_off_task(timeframe.to_date, "End Date", timeframe.type)


def get_correspondent_date_by_day(week_day):
    start_date = date(2023, 9, 18)  # Starting from 18th September 2023
    end_date = date(2023, 9, 24)  # Ending on 24th September 2023

    current_date = start_date
    while (
        current_date <= end_date
        and current_date.strftime("%A").lower() != week_day.lower()
    ):
        current_date += timedelta(days=1)
    return current_date


def convert_utc_to_timezone(timezone_name, utc_time_str):
    # Parse the input time string
    try:
        utc_time = datetime.strptime(f"2023-01-01 {utc_time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        utc_time = datetime.strptime(f"2023-01-01 {utc_time_str}", "%Y-%m-%d %H:%M")

    # Set the timezone for the parsed time to UTC
    utc_time = pytz.utc.localize(utc_time)

    # Convert to the desired timezone
    local_time = utc_time.astimezone(pytz.timezone(timezone_name))

    # Determine if a day was added, subtracted, or nothing changed
    if local_time.date() > utc_time.date():
        return "added"
    elif local_time.date() < utc_time.date():
        return "subtracted"
    else:
        return "nothing"


def get_day_to_store(UTC_time_str, timezone_str, week_day):
    date = get_correspondent_date_by_day(week_day)
    timezone_day_change = convert_utc_to_timezone(timezone_str, UTC_time_str)
    if timezone_day_change == "added":
        date -= timedelta(days=1)
    elif timezone_day_change == "subtracted":
        date += timedelta(days=1)
    return date.strftime("%A")


def get_day_to_send(UTC_time_str, timezone_str, week_day):
    date = get_correspondent_date_by_day(week_day)
    timezone_day_change = convert_utc_to_timezone(timezone_str, UTC_time_str)
    if timezone_day_change == "added":
        date += timedelta(days=1)
    elif timezone_day_change == "subtracted":
        date -= timedelta(days=1)
    return date.strftime("%A")
