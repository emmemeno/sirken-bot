import datetime
import pytz
import re


# Time stuff (boring!)
def find_date(line):
    date = re.search(r"(([12]\d{3})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01]))", line)
    if date:
        return {"year": int(date.group(2)), "month": int(date.group(3)), "day": int(date.group(4))}


def find_time(line):
    time = re.search("(([0-9]|0[0-9]|1[0-9]|2[0-3]):([0-5][0-9]))", line)
    if time:
        return {"hour": int(time.group(2)), "minute": int(time.group(3))}


def now():
    return datetime.datetime.utcnow().replace(second=0, microsecond=0)


def next_future(hours=1):
    return now() + datetime.timedelta(hours=hours)


def now_local(timezone):
    tz = pytz.timezone(timezone)
    return datetime.datetime.now(tz)


def from_mins_ago(mins):
    date_new = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    return date_new - datetime.timedelta(minutes=int(mins))


def convert24(time, meridian):
    if time["hour"] > 12:
        return False

    if meridian == "am":
        if time["hour"] == 12:
            time["hour"] = 00
    elif meridian == "pm":
        if not time["hour"] == 12:
            time["hour"] = time["hour"] + 12

    return time


def assemble_date(time_in, date_in, timezone='CET', days_back=0):

    # time is mandatory
    if not time_in:
        return False

    # try to validate the date
    try:
        # if both date and time are provided simply generate the date...
        date_assembled = datetime.datetime(year=date_in['year'],
                                     month=date_in['month'],
                                     day=date_in['day'],
                                     hour=time_in['hour'],
                                     minute=time_in['minute'])
        # ...and attach the timezone on it
        local_date = naive_to_tz(date_assembled, timezone)
    except:
        # if only time is provided, build it starting from local now
        date_now = now_local(timezone)
        local_date = date_now.replace(hour=time_in['hour'],
                                                      minute=time_in['minute'],
                                                      second=0,
                                                      microsecond=0)
        # if date is in the future, use yesterday
        if local_date > date_now:
            days_back = 1
        local_date = local_date - datetime.timedelta(days=days_back)

    utc_date = change_tz(local_date, "UTC")
    naive_date = tz_to_naive(utc_date)

    return naive_date


def naive_to_tz(naive_date, tz_to="UTC"):
    local = pytz.timezone(tz_to)
    return local.localize(naive_date)


def tz_to_naive(tz_date):
    return tz_date.replace(tzinfo=None)


def change_tz(mydate, target_timezone="CET"):
    tz_convert_to = pytz.timezone(target_timezone)
    return mydate.astimezone(tz_convert_to)


def change_naive_to_tz(mydate, ttz):
    mydate = naive_to_tz(mydate, "UTC")
    return change_tz(mydate, ttz)


def countdown(d_to, d_from):
    output = ""
    date_diff = d_from - d_to
    seconds_diff = date_diff.total_seconds()
    days = int(seconds_diff // (60 * 60 * 24))
    hours = int((seconds_diff - days*86400) // (60 * 60))
    minutes = int((seconds_diff // 60) % 60)
    if days == 1:
        output += "1 day "
    if days > 1:
        output += str(days) + " days "
    if hours == 1:
        output += "1 hour "
    if hours > 1:
        output += str(hours) + " hours "
    if hours and minutes:
        output += "and "
    if minutes == 1:
        output += "1 minute"
    if minutes > 1 or minutes == 0:
        output += str(minutes) + " minutes"

    return output
