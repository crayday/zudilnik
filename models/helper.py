import re
from datetime import datetime, date, time, timedelta
from config import Config


def parse_weekday_filter(weekday_filter: str) -> list[int]:
    """
    Parse the given weekday filter string
    and return a list of integer weekdays.

    The weekday filter string should contain comma-separated intervals
    or single days. Weekdays are represented by integers from 1 to 7,
    where 1 is Monday and 7 is Sunday. If filter is empty returns the whole
    week (from day 1 to day 7).

    Example:
        '_parse_weekday_filter("1-3,5,7")' will return [1, 2, 3, 5, 7]
    """
    if not weekday_filter:
        return list(range(1, 7+1))  # whole week, days 1 to 7

    weekdays = []
    intervals = weekday_filter.split(",")
    for interval in intervals:
        match = re.match(r"([1-7])-([1-7])$", interval)
        if match:
            from_day = int(match.group(1))
            to_day = int(match.group(2))
            for day in range(from_day, to_day + 1):
                weekdays.append(day)
        elif re.match(r"[1-7]$", interval):
            weekdays.append(int(interval))
        else:
            raise ValueError(f"Invalid weekday filter '{weekday_filter}'")
    return weekdays


def datetime_from_string(time_str: str) -> datetime:
    """
    Convert a time string to a datetime object.

    The function supports two formats:
    1. 'HH:MM' or 'HH:MM:SS': The time is assumed to be in the past 24 hours.
    2. 'YYYY.MM.DD HH:MM' or 'YYYY.MM.DD HH:MM:SS': The full date and time.

    If the time string doesn't match any of the supported formats,
        a ValueError is raised.

    Examples:
    1. datetime_from_string('12:34') -> datetime object representing 12:34
       today (or yesterday if the time is in the future).
    2. datetime_from_string('2021.09.01 12:34') -> datetime object representing
       September 1, 2021, 12:34.

    :param time_str: The time string to convert to a datetime object.
    :return: A datetime object representing the specified time.
    :raises ValueError: If the input string doesn't match any supported format.
    """
    if match := re.match(r'(\d{2}):(\d{2})(?::(\d{2}))?', time_str):
        now = datetime.now()
        second = int(match.group(3)) if match.group(3) else 0
        dt = now.replace(
            hour=int(match.group(1)),
            minute=int(match.group(2)),
            second=second
        )
        if dt > now:
            # Calculated time appeared in future.
            # Certanly time should refer to the previous day not to the future
            return dt - timedelta(days=1)
        else:
            return dt

    if match := re.match(
        r'(\d{4}).(\d{2}).(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?', time_str
    ):
        second = int(match.group(6)) if match.group(6) else 0
        return datetime(
            year=int(match.group(1)),
            month=int(match.group(2)),
            day=int(match.group(3)),
            hour=int(match.group(4)),
            minute=int(match.group(5)),
            second=second)

    raise ValueError(f"Doesn't support time string '{time_str}'")


def get_day_regarding_deadline(config: Config, dt: datetime) -> date:
    """
    Get the day which the given datetime belongs to regarding deadline.
    """
    deadline = time.fromisoformat(config.deadline_time)
    commitment_date = dt.date()

    if deadline < time(12):
        commitment_date -= timedelta(days=1)
    if dt.time() > deadline:
        commitment_date += timedelta(days=1)

    return commitment_date
