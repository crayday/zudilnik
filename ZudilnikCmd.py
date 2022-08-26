import cmd
import shlex
import re
from datetime import datetime

def get_param_number(line, begidx):
    reading_word = False
    found_param = False
    param_number = -1 # Don't count command name as a parameter
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
        param_number += 1;

    return param_number

def matching_options(text, options):
    return options if not text else [option for option in options if option.startswith(text)]

def cmd_prompt():
    return f"{datetime.now().strftime('%H:%M')}> "

def vprint(string): # verbose print
    print(f"{datetime.now().strftime('%H:%M')}: {string}")

def is_record_identifier(param):
    return re.fullmatch(r'(-?\d+|last|(pen)+ult)', param)

def matching_last_penult(text):
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

class ZudilnikCmd(cmd.Cmd):
    prompt = cmd_prompt()

    def __init__(self, zud):
        self.zud = zud
        super().__init__()

    def postcmd(self, stop, line):
        self.prompt = cmd_prompt()
        return stop

    def emptyline(self):
        pass

    def do_EOF(self, line):
        print()
        return True

    def do_exit(self, line):
        return True

    def complete_start(self, text, line, begidx, endidx):
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_projects(text)
        else:
            return []

    def do_start(self, line):
        params = shlex.split(line)
        subproject_name = params[0] if len(params) >= 1 else None
        comment = params[1] if len(params) >= 2 else None

        result = self.zud.start_subproject(subproject_name, comment=comment)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            vprint(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

        vprint(f"Started subproject #{result['subproject']['id']} {result['subproject']['name']}")

    def do_restart(self, line):
        params = shlex.split(line)
        comment = params[0] if len(params) >= 1 else None

        result = self.zud.start_subproject(None, comment=comment, restart_anyway=True)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            vprint(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

        vprint(f"Started subproject #{result['subproject']['id']} {result['subproject']['name']}")

    def do_stop(self, line):
        stoped_data = self.zud.stop_last_record()
        if stoped_data:
            vprint(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

    def complete_del(self, *args):
        return self.complete_delete(*args)

    def do_del(self, line): # shortcut for delete
        return self.do_delete(line)

    def complete_delete(self, text, line, begidx, endidx):
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return matching_last_penult(text)
    
    def do_delete(self, line):
        params = shlex.split(line)
        record_id = params[0]
        data = self.zud.delete_record(record_id)
        vprint(f"Deleted record #{data['record_id']}")

    def complete_comment(self, text, line, begidx, endidx):
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return matching_last_penult(text)

    def do_comment(self, line):
        """comment <text> | comment <record_id> <text> - comments a given record or the last record if not specified"""
        params = shlex.split(line)
        if len(params) >= 2:
            record_id = params[0]
            comment = params[1]
        else:
            record_id = 'last'
            comment = params[0]

        data = self.zud.comment_record(record_id, comment)

        vprint(f"Updated comment for record #{data['record_id']} started at {data['record_started_at']}")

    set_fields = ['start', 'started', 'stop', 'stoped', 'project']

    def complete_set(self, text, line, begidx, endidx):
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
            return self.zud.find_projects(text)
        else:
            return []

    def do_set(self, line):
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
            data = self.zud.set_record_start_time(record_id, time_str)
            if data['duration']:
                vprint(f"Updated record #{data['record_id']}, now started at {data['started_at']}, duration {data['duration']}")
            else:
                vprint(f"Updated record #{data['record_id']}, now started at {data['started_at']}")
        elif field == 'stoped' or field == 'stop':
            time_str = value
            data = self.zud.set_record_stop_time(record_id, time_str)
            vprint(f"Updated record #{data['record_id']}, now stoped at {data['stoped_at']}, duration {data['duration']}")
        elif field == 'project':
            project_name = value
            data = self.zud.set_record_project(record_id, project_name)
            vprint(f"Updated project for record #{data['record_id']}")
        else:
            raise Exception("unknown field '"+field+"' to set")

        if comment:
            self.zud.comment_record(record_id, comment)

    def do_np(self, line): # shortcut for newproject
        return self.do_newproject(line)

    def do_newproject(self, line):
        (project_name) = shlex.split(line)
        project_id = self.zud.add_new_project(project_name)
        vprint(f'Added project "{project_name}" #{project_id}')

    def complete_new(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_root_projects(text)
        else:
            return []
    
    def do_new(self, line):
        (project_name, subproject_name) = shlex.split(line)
        subproject_id = self.zud.add_new_subproject(project_name, subproject_name)
        vprint(f'Added subproject "{subproject_name}" #{subproject_id}')

    def complete_ls(self, *args):
        return self.complete_list(*args)

    def do_ls(self, line): # shortcut for list
        return self.do_list(line)

    def complete_list(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_root_projects(text)
        else:
            return []

    def do_list(self, line):
        params = shlex.split(line)
        project_name = params[0] if len(params) >= 1 else 0
        if project_name:
            # concrete project given - need to list all it's subprojects
            projects = self.zud.get_subprojects(project_name)
        else:
            # no project given - need to list all projects
            projects = self.zud.get_projects()
        for project in projects:
            vprint(f"#{project['id']} {project['name']}")

    def do_tl(self, line): # shortcut for timelog
        return self.do_timelog(line)
    
    def do_timelog(self, line):
        params = shlex.split(line)
        limit = params[0] if len(params) >= 1 else 12
        timelog = self.zud.get_timelog(limit)
        for day in timelog:
            print(day)
            for row in timelog[day]:
                print(f"#{row['id']} {row['started_at']}-{row['stoped_at']}: "+
                      f"[{row['project']}/{row['subproject']}] - "+
                      f"{row['comment']} ({row['duration']})")
            print('')

    def complete_ng(self, *args):
        return self.complete_newgoal(*args)

    def do_ng(self, line): # shortcut for newgoal
        return self.do_newgoal(line)

    def complete_newgoal(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_root_projects(text)
        else:
            return []

    def do_newgoal(self, line):
        """newgoal <project_name> <goal_name> <goal_type> - creates new goal to work on a given project. goal_type maybe hours_light (default) or hours_mandatory."""
        params = shlex.split(line)
        project_name = params[0]
        goal_name = params[1]
        goal_type = params[2] if len(params) > 2 else 'hours_light'
        goal_id = self.zud.add_new_goal(project_name, goal_name, goal_type)
        vprint(f'Added goal "{goal_name}" #{goal_id}')

    def complete_setgoal(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_goals(text)
        elif param_number == 2:
            return matching_options(text, ['type'])
        elif param_number == 3:
            return matching_options(text, ['hours_light', 'hours_mandatory'])
        else:
            return []

    def do_setgoal(self, line):
        """setgoal <goal_name> type (hours_light|hours_mandatory)"""
        params = shlex.split(line)
        goal_name = params[0]
        field = params[1]
        value = params[2]
        if field == 'type':
            self.zud.set_goal_type(goal_name, value)

    def complete_archivegoal(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_goals(text)
        else:
            return []

    def do_archivegoal(self, line):
        """archivegoal <goal_name>"""
        params = shlex.split(line)
        goal_name = params[0]
        self.zud.archive_goal(goal_name)

    def complete_hpd(self, *args):
        return self.complete_hoursperday(*args)

    def do_hpd(self, line): # shortcut for hoursperday
        """short for hoursperday"""
        return self.do_hoursperday(line)

    def complete_hoursperday(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_goals(text)
        else:
            return []

    def do_hoursperday(self, line):
        """hoursperday <goal_name> <hours> <from>-<to> - commits to work on a goal for a given number of hours at a given days range. 1 is monday. 7 is sunday. if <to> day is omitted than commiting to work on a single given day."""
        params = shlex.split(line)
        goal_name = params[0]
        hours = params[1]
        weekday_filter = params[2] if len(params) > 2 else None

        self.zud.set_hours_per_day(goal_name, hours, weekday_filter)

        vprint(f"Commited to work on '{goal_name}' for {hours} hours on days {weekday_filter}")

    def do_gi(self, line): # shortcut for goalsinfo
        return self.do_goalsinfo(line)

    def do_goalsinfo(self, line):
        goals_info = self.zud.get_goals_info()
        for goal in goals_info:
            print(f"# {goal['name']}")
            if goal['status'] == 'due':
                print(f"DUE {goal['duration']} more before {goal['deadline']}")
            else:
                print(f"OVERWORKED goal by {goal['duration']}")

            print(f"(goal started at {goal['started']}, "
                f"hours per day: {goal['last_hours_per_day']}, "
                f"worked today {goal['total_worked_today']}, "
                f"total {goal['total_worked']})")

    def complete_worked(self, text, line, begidx, endidx):
        (command, *params) = shlex.split(line)
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return self.zud.find_goals(text)
        else:
            return []

    def do_worked(self, line):
        params = shlex.split(line)
        goal_name = params[0]
        from_date = params[1]
        to_date = params[2] if len(params) >= 3 else from_date
        worked_time, from_dt, to_dt = self.zud.worked_on_goal2(goal_name, from_date, to_date)
        print(f"worked {worked_time} from {from_dt} to {to_dt} on {goal_name}")

    def do_wp(self, *params):
        return self.do_workedproject(*params)

    def do_workedproject(self, line):
        params = shlex.split(line)
        project_name = params[0]
        from_date = params[1]
        to_date = params[2] if len(params) >= 3 else from_date
        # FIXME TODO worked_on_project instead of worked_on_goal2
        worked_time, from_dt, to_dt = self.zud.worked_on_goal2(project_name, from_date, to_date)
        print(f"worked {worked_time} from {from_dt} to {to_dt} on {project_name}")
