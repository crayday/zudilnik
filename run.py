import sys
import sqlite3
import shlex
from datetime import datetime, timedelta, time as dttime, date as dtdate
from Zudilnik import Zudilnik

verbose=True

def vprint(string, time=True): # verbose print
    if verbose:
        if time:
            print('{}: {}'.format(datetime.now().strftime('%H:%M'), string))
        else:
            print(string)

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
        subproject_name = params[0] if len(params) >= 1 else None
        comment = params[1] if len(params) >= 2 else None
        restart_anyway = (command == 'restart')
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
            print('# '+goal['name'])
            if goal['status'] == 'due':
                print("DUE {} more before {}".format(
                    goal['duration'], goal['deadline']
                ))
            else:
                print("OVERWORKED goal by {}".format(
                    goal['duration']
                ))

            print(
                "(goal started at {}, hours per day: {}, worked today {}, total {})".format(
                goal['started'], goal['last_hours_per_day'],
                goal['total_worked_today'], goal['total_worked']
            ))
    
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
        if len(params) >= 3:
            record_id = params[0]
            field = params[1]
            value = params[2]
        else:
            record_id = 'last'
            field = params[0]
            value = params[1]

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
    else:
        raise Exception("unknown command "+command)

    con.commit()

con = sqlite3.connect("db.sqlite3")
con.row_factory = sqlite3.Row
cur = con.cursor()

deadline=dttime(7, 15) # 07:15 AM
zudilnik = Zudilnik(cur, deadline, )

if len(sys.argv) >= 2:
    (script_name, command, *params) = sys.argv
    parse_command(zudilnik, command, params)
else:
    while True:
        command_string = input('> ')
        if command_string.strip():
            try:
                (command, *params) = shlex.split(command_string)
                if command == 'exit':
                    break
                else:
                    try:
                        parse_command(zudilnik, command, params)
                    except Exception as e:
                        print("Error: "+str(e))
            except ValueError as e:
                print("Invalid input: "+str(e))
