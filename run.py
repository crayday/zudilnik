import sys
import shlex
from datetime import datetime, timedelta, time as dttime, date as dtdate
from Zudilnik import Zudilnik

verbose=True

def main():
    deadline=dttime(7, 15) # 07:15 AM
    zudilnik = Zudilnik(deadline)

    if len(sys.argv) >= 2:
        (script_name, command, *params) = sys.argv
        parse_command(zudilnik, command, params)
    else:
        while True:
            try:
                command_string = input('> ')
                if command_string.strip():
                    (command, *params) = shlex.split(command_string)
                    if command == 'exit':
                        break
                    else:
                        try:
                            parse_command(zudilnik, command, params)
                        except Exception as e:
                            vprint("Error: "+str(e))
            except ValueError as e:
                vprint("Invalid input: "+str(e))
            except UnicodeDecodeError as e:
                vprint("Something wrong with input encoding: "+str(e))

def parse_command(zudilnik, command, params):
    if command == 'newproject' or command == 'np':
        project_name = params[0]
        project_id = zudilnik.add_new_project(project_name)
        vprint('Added project "{}" #{}'.format(project_name, project_id))

    elif command == 'newsubproject' or command == 'new':
        (project_name, subproject_name) = params
        subproject_id = zudilnik.add_new_subproject(project_name, subproject_name)
        vprint('Added subproject "{}" #{}'.format(subproject_name, subproject_id))

    elif command == 'start' or command == 'restart':
        if command == 'restart':
            subproject_name = None
            comment = params[0] if len(params) >= 1 else None
            restart_anyway = True
        else:
            subproject_name = params[0] if len(params) >= 1 else None
            comment = params[1] if len(params) >= 2 else None
            restart_anyway = False

        result = zudilnik.start_subproject(subproject_name, comment=comment, restart_anyway=restart_anyway)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            vprint('Stoped record #{} started at {}, duration {}'.format(
                stoped_data['last_record_id'], stoped_data['started_at'],
                stoped_data['duration']
            ))

        vprint('Started subproject #{} {}'.format(result['subproject']['id'], result['subproject']['name']))

    elif command == 'stop':
        stoped_data = zudilnik.stop_last_record()
        if stoped_data:
            vprint('Stoped record #{} started at {}, duration {}'.format(
                stoped_data['last_record_id'], stoped_data['started_at'],
                stoped_data['duration']
            ))

    elif command == 'comment':
        if len(params) >= 2:
            record_id = params[0]
            comment = params[1]
        else:
            record_id = 'last'
            comment = params[0]

        if record_id == 'last':
            data = zudilnik.comment_last_record(comment)
        else:
            data = zudilnik.comment_record(record_id, comment)

        vprint('Updated comment for record #{} started at {}'.format(
            data['record_id'], data['record_started_at']
        ))

    elif command == 'delete' or command == 'del':
        record_id = params[0]
        if record_id == 'last':
            data = zudilnik.delete_last_record()
        else:
            data = zudilnik.delete_record(int(record_id))
        vprint('Deleted record #{}'.format(data['record_id']))

    elif command == 'newgoal' or command == 'ng':
        (project_name, goal_name) = params
        goal_type = params[2] if len(params) > 2 else 'hours_light'
        goal_id = zudilnik.add_new_goal(project_name, goal_name, goal_type)
        vprint('Added goal "{}" #{}'.format(goal_name, goal_id))

    elif command == 'hoursperday' or command == 'hpd':
        goal_name = params[0]
        hours = params[1]
        weekday_filter = params[2] if len(params) > 2 else None

        zudilnik.set_hours_per_day(goal_name, hours, weekday_filter)

        vprint("Commited to work on '{}' for {} hours on days {}".format(goal_name, hours, weekday_filter))

    elif command == 'goalsinfo' or command == 'gi':
        goals_info = zudilnik.get_goals_info()
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

    elif command == 'worked':
        goal_name = params[0]
        from_date = params[1]
        to_date = params[2] if len(params) >= 3 else from_date
        worked_time, from_dt, to_dt = zudilnik.worked_on_goal2(goal_name, from_date, to_date)
        print(f"worked {worked_time} from {from_dt} to {to_dt} on {goal_name}")
    
    elif command == 'timelog' or command == 'tl':
        limit = params[0] if len(params) >= 1 else 12
        timelog = zudilnik.get_timelog(limit)
        for day in timelog:
            print(day)
            for row in timelog[day]:
                print('#{} {}-{}: [{}/{}] - {} ({})'.format(
                    row['id'], row['started_at'], row['stoped_at'], row['project'],
                    row['subproject'], row['comment'], row['duration']
                ))
            print('')

    elif command == 'list' or command == 'ls':
        project_name = params[0] if len(params) >= 1 else 0
        if project_name:
            # concrete project given - need to list all it's subprojects
            projects = zudilnik.get_subprojects(project_name)
        else:
            # no project given - need to list all projects
            projects = zudilnik.get_projects()
        for project in projects:
            print('#{} {}'.format(project['id'], project['name']))

    elif command == 'set':
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
                data = zudilnik.set_last_record_start_time(time_str)
            else:
                data = zudilnik.set_record_start_time(int(record_id), time_str)
            if data['duration']:
                vprint('Updated record #{}, now started at {}, duration {}'.format(
                    data['record_id'], data['started_at'],
                    data['duration']
                ))
            else:
                vprint('Updated record #{}, now started at {}'.format(
                    data['record_id'], data['started_at'],
                ))
        elif field == 'stoped' or field == 'stop':
            time_str = value
            if record_id == 'last':
                data = zudilnik.set_last_record_stop_time(time_str)
            else:
                data = zudilnik.set_record_stop_time(int(record_id), time_str)
            vprint('Updated record #{}, now stoped at {}, duration {}'.format(
                data['record_id'], data['stoped_at'],
                data['duration']
            ))
        elif field == 'project':
            project_name = value
            if record_id == 'last':
                data = zudilnik.set_last_record_project(project_name)
            else:
                data = zudilnik.set_record_project(int(record_id), project_name)
            vprint('Updated project for record #{}'.format(data['record_id']))
        else:
            raise Exception("unknown field '"+field+"' to set")

        print(f"hello {comment}!") # FIXME
        if comment and record_id == 'last':
            zudilnik.comment_last_record(comment)
        elif comment:
            zudilnik.comment_record(record_id, comment)
        print("hello again!") # FIXME
    else:
        raise Exception("unknown command "+command)

def vprint(string, time=True): # verbose print
    if verbose:
        if time:
            print('{}: {}'.format(datetime.now().strftime('%H:%M'), string))
        else:
            print(string)

main()
