from datetime import datetime
import shlex
from .base import BaseCommand
from models import Project, TimeLog
from .helper import (
    n_params_from_line, get_param_number, matching_options,
    is_record_identifier, matching_last_penult, seconds_to_hms
)
from models.helper import get_day_regarding_deadline


class TimeLogCommand(BaseCommand):
    def complete_start(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Project.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_start(self, line: str) -> None:
        project_name, comment = n_params_from_line(line, 2)

        result = TimeLog.start_project(
            self.app, self.current_user_id, project_name, comment=comment
        )

        if result and result.stoped_record:
            self.print_about_stoped_record(result.stoped_record)

        self.print_w_time(
            f"Started project #{result.started_project.id} "
            f"{result.started_project.name}"
        )

    def do_restart(self, line: str) -> None:
        (comment,) = n_params_from_line(line, 1)

        result = TimeLog.start_project(
            self.app,
            self.current_user_id,
            comment=comment,
            restart_anyway=True
        )

        if result and result.stoped_record:
            self.print_about_stoped_record(result.stoped_record)

        self.print_w_time(
            f"Started project #{result.started_project.id} "
            f"{result.started_project.name}"
        )

    def do_stop(self, line: str) -> None:
        stoped_record = TimeLog.stop_last_record(
            self.app, self.current_user_id)
        if stoped_record:
            self.print_about_stoped_record(stoped_record)

    def print_about_stoped_record(self, stoped_record: TimeLog) -> None:
        started_at_dt = datetime.fromtimestamp(stoped_record.started_at)
        self.print_w_time(
            f"Stoped record #{stoped_record.id} "
            f"started at {started_at_dt.strftime('%F %T')}, "
            f"duration {seconds_to_hms(stoped_record.duration)}"
        )

    def complete_del(self, *args) -> list[str]:
        return self.complete_delete(*args)

    def do_del(self, line: str) -> None:
        """shortcut for delete"""
        return self.do_delete(line)

    def complete_delete(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return matching_last_penult(text)

    def do_delete(self, line: str) -> None:
        (record_identifier,) = n_params_from_line(line, 1)
        deleted_record = TimeLog.delete_record(
            self.app, self.current_user_id, record_identifier
        )
        self.print_w_time(f"Deleted record #{deleted_record.id}")

    def complete_comment(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return matching_last_penult(text)

    def do_comment(self, line: str) -> None:
        """comment <text> | comment <record_id> <text> - comments a given record or the last record if not specified"""
        (record_identifier, comment) = n_params_from_line(line, 2)
        if comment is None:
            comment, record_identifier = record_identifier, 'last'

        updated_record = TimeLog.comment_record(
            self.app, self.current_user_id, record_identifier, comment
        )

        started_at_dt = datetime.fromtimestamp(updated_record.started_at)
        self.print_w_time(
            f"Updated comment for record #{updated_record.id} "
            f"started at {started_at_dt.strftime('%F %T')}"
        )

    set_fields = ['start', 'started', 'stop', 'stoped', 'project']

    def complete_set(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)

        if param_number == 1 or param_number == 2 and is_record_identifier(params[0]):
            options = matching_options(text, self.set_fields)
            if param_number == 1 and len(options) == 0:
                return matching_last_penult(text)
            else:
                return options
        elif param_number == 2 and params[0] == 'project' \
                or param_number == 3 and params[1] == 'project':
            return Project.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_set(self, line: str) -> None:
        params = shlex.split(line)

        if len(params) >= 3 and params[1] in self.set_fields:
            record_id = params[0]
            field = params[1]
            value = params[2]
            comment = params[3] if len(params) >= 4 else None
        else:
            record_id = 'last'
            field = params[0]
            value = params[1]
            comment = params[2] if len(params) >= 3 else None

        if field == 'started' or field == 'start':
            time_str = value
            updated_record = TimeLog.set_record_start_time(
                self.app, self.current_user_id, record_id, time_str
            )
            started_at_dt = datetime.fromtimestamp(updated_record.started_at)
            message = (
                f"Updated record #{updated_record.id}, "
                f"now started at {started_at_dt.strftime('%F %T')}"
            )
            if updated_record.duration:
                duration = seconds_to_hms(updated_record.duration)
                message += f", duration {duration}"
            self.print_w_time(message)

        elif field == 'stoped' or field == 'stop':
            time_str = value
            updated_record = TimeLog.set_record_stop_time(
                self.app, self.current_user_id, record_id, time_str
            )
            stoped_at_dt = datetime.fromtimestamp(updated_record.stoped_at)
            self.print_w_time(
                f"Updated record #{updated_record.id}, "
                f"now stoped at {stoped_at_dt.strftime('%F %T')}, "
                f"duration {seconds_to_hms(updated_record.duration)}"
            )

        elif field == 'project':
            project_name = value
            updated_record = TimeLog.set_record_project(
                self.app, self.current_user_id, record_id, project_name
            )
            self.print_w_time(
                f"Updated project for record #{updated_record.id}"
            )
        else:
            raise Exception("unknown field '"+field+"' to set")

        if comment:
            TimeLog.comment_record(
                self.app, self.current_user_id, record_id, comment
            )

    def do_tl(self, line: str) -> None:
        """Short for timelog"""
        return self.do_timelog(line)

    def do_timelog(self, line: str) -> None:
        """timelog <limit> - extract <limit> number of rows (12 by default)"""
        (limit,) = n_params_from_line(line, 1)
        if not limit:
            limit = 12

        timelog = TimeLog.get_timelog(
            self.app, self.current_user_id, page_size=int(limit)
        )
        seen_days = set()
        for record, project in timelog:
            started_at_dt = datetime.fromtimestamp(record.started_at)
            day = get_day_regarding_deadline(
                self.app.config, started_at_dt
            ).isoformat()

            if day not in seen_days:
                # Print a blank line before every day other than first
                if seen_days:
                    self.print('')
                self.print(day)
                seen_days.add(day)

            if record.stoped_at:
                stoped_at_dt = datetime.fromtimestamp(record.stoped_at)
                stoped_at = stoped_at_dt.strftime("%H:%M")
                duration = record.duration
            else:
                stoped_at = '.....'
                duration = (
                    int(self.app.now().timestamp()) - record.started_at
                )

            comment = record.comment if record.comment else '...'
            started_at = started_at_dt.strftime("%H:%M")

            self.print(
                f"#{record.id} {started_at}-{stoped_at}: "
                f"[{project.name}] - "
                f"{comment} ({seconds_to_hms(duration)})"
            )
