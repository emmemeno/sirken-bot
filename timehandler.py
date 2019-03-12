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
    date_new = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    return naive_to_tz(date_new, 'UTC', 'UTC')


def from_mins_ago(mins):
    date_new = datetime.datetime.utcnow().replace(second=0, microsecond=0)
    return naive_to_tz(date_new - datetime.timedelta(minutes=int(mins)), 'UTC', 'UTC')


def assemble_date(s, timezone='CET'):
    if re.search(r"\b(now)\b", s):
        return now()

    regex_str = r"\b(\d+) ?(mins?|minutes?) ago"
    mins_ago = re.search(regex_str, s)
    if mins_ago:
        return from_mins_ago(mins_ago.group(1))

    time_in = find_time(s)
    date_in = find_date(s)
    # time is mandatory
    if not time_in:
        return False

    # try to validate the date
    try:
        date_new = datetime.datetime(year=date_in['year'],
                                     month=date_in['month'],
                                     day=date_in['day'],
                                     hour=time_in['hour'],
                                     minute=time_in['minute'])
    except:
        # if date is not provided, use actual date and replace hour and minute
        date_new = datetime.datetime.utcnow().replace(hour=time_in['hour'],
                                                      minute=time_in['minute'],
                                                      second=0,
                                                      microsecond=0)
    return naive_to_tz(date_new, timezone, 'UTC')


def naive_to_tz(mydate, tz_from="CET", tz_to="CET"):
    local = pytz.timezone(tz_from)
    current_date = local.localize(mydate)
    tz_convert_to = pytz.timezone(tz_to)
    return current_date.astimezone(tz_convert_to)


def change_tz(mydate, target_timezone="CET"):
    tz_convert_to = pytz.timezone(target_timezone)
    return mydate.astimezone(tz_convert_to)


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
