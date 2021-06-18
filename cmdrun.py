import cmd
import shlex
import re
from datetime import datetime, timedelta, time as dttime, date as dtdate
from Zudilnik import Zudilnik

def get_param_number(line):
    (command, *params) = shlex.split(line)
    param_number = len(params)
    if re.search(r'\s$', line):
        param_number+=1
    return param_number

def matching_options(text, options):
    return options if not text else [option for option in options if option.startswith(text)]

def cmd_prompt():
    return f"{datetime.now().strftime('%H:%M')}> "

def try_split_params(line):
    try:
        params = shlex.split(line)
    except Exception:
        params = []
    return params

def runcmd_uninterrupted(cmdobj):
    try:
        cmdobj.cmdloop()
    except Exception as e:
        print("Error: "+str(e))
        runcmd_uninterrupted(cmdobj)

class ZudilnikCmd(cmd.Cmd):
    prompt = cmd_prompt()

    def __init__(self, zud):
        self.zud = zud
        super().__init__()

    def precmd(self, line):
        params = try_split_params(line)
        is_exit_command = len(params) > 0 and params[0] in ['exit', 'EOF']
        if len(line) != 0 and not is_exit_command:
            print(datetime.now().strftime('%H:%M')+" ", end='')
        return line

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

    def complete_hline(self, text, line, begidx, endidx):
        param_number = get_param_number(line)
        if param_number == 1: # подсказываем 1-ый аргумент name
            return matching_options(text, ['Yegor', 'Yulia', 'Eugene', 'Hish'])
        elif param_number == 2: # подсказываем 2-ой аргумент word
            return matching_options(text, ['common', 'heal', 'gore', 'less', 'wisdom', 'welcome', 'goodbye', 'kill'])
        else:
            return []

    def do_start(self, line):
        params = shlex.split(line)
        subproject_name = params[0] if len(params) >= 1 else None
        comment = params[1] if len(params) >= 2 else None

        result = self.zud.start_subproject(subproject_name, comment=comment)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            print(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

        print(f"Started subproject #{result['subproject']['id']} {result['subproject']['name']}")

    def do_restart(self, line):
        params = shlex.split(line)
        comment = params[0] if len(params) >= 1 else None

        result = self.zud.start_subproject(None, comment=comment, restart_anyway=True)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            print(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

        print(f"Started subproject #{result['subproject']['id']} {result['subproject']['name']}")

    def do_stop(self, line):
        stoped_data = self.zud.stop_last_record()
        if stoped_data:
            print(f"Stoped record #{stoped_data['last_record_id']} started at {stoped_data['started_at']}, duration {stoped_data['duration']}")

    def do_delete(self, line):
        params = shlex.split(line)
        record_id = params[0]
        if record_id == 'last':
            data = self.zud.delete_last_record()
        else:
            data = self.zud.delete_record(int(record_id))
        print(f"Deleted record #{data['record_id']}")

    def do_comment(self, line):
        """comment <text> | comment <record_id> <text> - comments a given record or the last record if not specified"""
        params = shlex.split(line)
        if len(params) >= 2:
            record_id = params[0]
            comment = params[1]
        else:
            record_id = 'last'
            comment = params[0]

        if record_id == 'last':
            data = self.zud.comment_last_record(comment)
        else:
            data = self.zud.comment_record(record_id, comment)

        print(f"Updated comment for record #{data['record_id']} started at {data['record_started_at']}")

    def do_set(self, line):
        params = shlex.split(line)

        fields = ['start', 'started', 'stop', 'stoped', 'project']
        if len(params) >= 3 and params[1] in fields:
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
            if record_id == 'last':
                data = self.zud.set_last_record_start_time(time_str)
            else:
                data = self.zud.set_record_start_time(int(record_id), time_str)
            if data['duration']:
                print(f"Updated record #{data['record_id']}, now started at {data['started_at']}, duration {data['duration']}")
            else:
                print(f"Updated record #{data['record_id']}, now started at {data['started_at']}")
        elif field == 'stoped' or field == 'stop':
            time_str = value
            if record_id == 'last':
                data = self.zud.set_last_record_stop_time(time_str)
            else:
                data = self.zud.set_record_stop_time(int(record_id), time_str)
            print(f"Updated record #{data['record_id']}, now stoped at {data['stoped_at']}, duration {data['duration']}")
        elif field == 'project':
            project_name = value
            if record_id == 'last':
                data = self.zud.set_last_record_project(project_name)
            else:
                data = self.zud.set_record_project(int(record_id), project_name)
            print(f"Updated project for record #{data['record_id']}")
        else:
            raise Exception("unknown field '"+field+"' to set")

        if comment and record_id == 'last':
            self.zud.comment_last_record(comment)
        elif comment:
            self.zud.comment_record(record_id, comment)

    def do_worked(self, line):
        params = shlex.split(line)
        goal_name = params[0]
        from_date = params[1]
        to_date = params[2] if len(params) >= 3 else from_date
        worked_time, from_dt, to_dt = self.zud.worked_on_goal2(goal_name, from_date, to_date)
        print(f"worked {worked_time} from {from_dt} to {to_dt} on {goal_name}")

deadline=dttime(7, 15) # 07:15 AM
zudcmd = ZudilnikCmd(Zudilnik(deadline))
runcmd_uninterrupted(zudcmd)
