from datetime import datetime
import re
import shlex
from models import GoalType


def n_params_from_line(line: str, count: int) -> list[str]:
    params = shlex.split(line)
    while len(params) < count:
        params.append(None)
    return params


def get_param_number(line: str, begidx: int) -> int:
    reading_word = False
    found_param = False
    param_number = -1  # Don't count command name as a parameter
    for i, char in enumerate(line):
        is_whitespace = re.search(r'\s', char)
        if is_whitespace and reading_word:
            reading_word = False
        elif not is_whitespace and not reading_word:
            reading_word = True
            param_number += 1

        if i == begidx:
            found_param = True
            break

    if not found_param:
        param_number += 1

    return param_number


def matching_options(text: str, options: list[str]) -> list[str]:
    if not text:
        return options
    return [option for option in options if option.startswith(text)]


def is_record_identifier(param: str) -> bool:
    return re.fullmatch(r'(-?\d+|last|(pen)+ult)', param)


def matching_last_penult(text: str) -> list[str]:
    if len(text) == 0:
        return ["last", "penult"]
    if "last".startswith(text):
        return ["last"]
    m = re.fullmatch(r'((pen)*)pe?n?', text)
    if m:
        return [m.group(1)+"penult", m.group(1)+"penpenult"]
    m = re.fullmatch(r'((pen)*)ul?t?', text)
    if m:
        return [m.group(1)+"ult"]
    return []


def get_goal_type_names() -> list[str]:
    return [key.lower() for key in GoalType.__members__.keys()]


def seconds_to_hms(seconds: int) -> str:
    """
    Convert seconds to a human-readable hours, minutes, and seconds string.

    Example:
        seconds_to_hms(3666) -> "1h 1m 6s"
    """
    remain_seconds = int(seconds % 60)
    minutes = int(seconds // 60)
    remain_minutes = int(minutes % 60)
    hours = int(minutes // 60)
    parts = []
    if hours:
        parts.append(str(hours)+'h')
    if remain_minutes:
        parts.append(str(remain_minutes)+'m')
    if remain_seconds:
        parts.append(str(remain_seconds)+'s')
    if parts:
        return ' '.join(parts)
    else:
        return '0'
