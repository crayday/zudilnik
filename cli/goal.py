from sqlalchemy.exc import ArgumentError
from .base import BaseCommand
from models import Project, Goal, GoalType, Commitment
from .helper import (
    n_params_from_line, get_param_number, matching_options, get_goal_type_names
)


class GoalCommand(BaseCommand):
    def complete_ng(self, *args) -> list[str]:
        return self.complete_newgoal(*args)

    def do_ng(self, line: str) -> None:
        """shortcut for newgoal"""
        return self.do_newgoal(line)

    def complete_newgoal(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Project.find_root_projects(
                self.app, self.current_user_id, text)
        elif param_number == 3:
            return matching_options(text, get_goal_type_names())
        else:
            return []

    def do_newgoal(self, line: str) -> None:
        """newgoal <project_name> <goal_name> <goal_type> - creates new goal to work on a given project. goal_type maybe hours_light (default) or hours_mandatory."""
        (project_name, goal_name, goal_type) = n_params_from_line(line, 3)
        try:
            goal_type_enum = (
                GoalType(goal_type) if goal_type else GoalType.HOURS_LIGHT
            )
            goal_id = Goal.add_new(
                self.app, self.current_user_id, project_name,
                goal_name, goal_type_enum)
            self.print_w_time(f'Added goal "{goal_name}" #{goal_id}')
        except (ValueError, ArgumentError) as e:
            self.print_w_time(f"Invalid input: '{e}'")

    def complete_setgoal(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Goal.find_by_name(
                self.app, self.current_user_id, text)
        elif param_number == 2:
            return matching_options(text, ['type'])
        elif param_number == 3:
            return matching_options(text, get_goal_type_names())
        else:
            return []

    def do_setgoal(self, line: str) -> None:
        """setgoal <goal_name> type (hours_light|hours_mandatory)"""
        (goal_name, field, value) = n_params_from_line(line, 3)
        if field == 'type':
            try:
                Goal.set_type_by_name(
                    self.app,
                    self.current_user_id,
                    goal_name,
                    GoalType(value)
                )
            except (ValueError, TypeError) as e:
                self.print_w_time(f"Invalid input: '{e}'")

    def complete_archivegoal(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Goal.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_archivegoal(self, line: str) -> None:
        """archivegoal <goal_name>"""
        (goal_name,) = n_params_from_line(line, 1)
        try:
            Goal.archive_by_name(self.app, self.current_user_id, goal_name)
        except (ValueError, TypeError) as e:
            self.print_w_time(f"Invalid input: '{e}'")

    def complete_hpd(self, *args) -> list[str]:
        return self.complete_hoursperday(*args)

    def do_hpd(self, line: str) -> None:
        """short for hoursperday"""
        return self.do_hoursperday(line)

    def complete_hoursperday(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Goal.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_hoursperday(self, line: str) -> None:
        """hoursperday <goal_name> <hours> <from>-<to> - commit to work on the goal for the given number of hours within the specified days range. 1 is Monday, and 7 is Sunday. If the <to> day is omitted, then commit to work on a single specified day."""
        (goal_name, hours, weekday_filter) = n_params_from_line(line, 3)

        try:
            Commitment.set_hours_per_day(
                self.app,
                self.current_user_id,
                goal_name,
                hours,
                weekday_filter
            )

            self.print_w_time(
                f"Commited to work on '{goal_name}' for {hours} hours "
                f"on days {weekday_filter}"
            )
        except ValueError as e:
            self.print_w_time(f"Invalid input: '{e}'")

    def do_gi(self, line: str) -> None:
        """shortcut for goalsinfo"""
        return self.do_goalsinfo(line)

    def do_goalsinfo(self, line: str) -> None:
		pass  # TODO
        # goals_info = self.zud.get_goals_info()
        # for goal in goals_info:
        #     print(f"# {goal['name']}")
        #     if goal['status'] == 'due':
        #         print(f"DUE {goal['duration']} more before {goal['deadline']}")
        #     else:
        #         print(f"OVERWORKED goal by {goal['duration']}")

        #     print(f"(goal started at {goal['started']}, "
        #           f"hours per day: {goal['last_hours_per_day']}, "
        #           f"worked today {goal['total_worked_today']}, "
        #           f"total {goal['total_worked']})")

    def complete_worked(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Goal.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_worked(self, line: str) -> None:
        goal_name, from_date, to_date = n_params_from_line(line, 3)
        if not to_date:
            to_date = from_date
		pass  # TODO
        # worked_time, from_dt, to_dt = self.zud.worked_on_goal2(
        #     goal_name, from_date, to_date)
        # print(f"worked {worked_time} from {from_dt} to {to_dt} on {goal_name}")

    def complete_wp(self, *args) -> list[str]:
        return self.complete_workedproject(*args)

    def do_wp(self, *params) -> None:
        """short for workedproject"""
        return self.do_workedproject(*params)

    def complete_workedproject(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        param_number = get_param_number(line, begidx)
        if param_number == 1:  # project_name
            return Project.find_by_name(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_workedproject(self, line: str) -> None:
        """workedproject <project> <from> <to> - how much time worked on project named <project> from date <from> and to date <to>. Date can be in form YYYY-MM-DD or MM-DD or DD. One digit day or month can be used too. Separator can be any."""
        project_name, from_date, to_date = n_params_from_line(line, 3)
        if not to_date:
            to_date = from_date
		pass  # TODO
        # worked_time, from_dt, to_dt = self.zud.worked_on_project(project_name, from_date, to_date)
        # print(f"worked {worked_time} from {from_dt} to {to_dt} on {project_name}")
