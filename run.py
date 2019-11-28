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

    elif command == 'start':
        subproject_name = params[0]
        comment = params[1] if len(params) >= 2 else None
        result = zudilnik.start_subproject(subproject_name, comment = None)
        if result and result['stoped_last_record']:
            stoped_data = result['stoped_last_record']
            vprint('Stoped record #{} started at {}, duration {}'.format(
                stoped_data['last_record_id'], stoped_data['started_at'],
                stoped_data['duration']
            ))

        vprint('Started subproject #{}'.format(result['subproject']['id']))

    elif command == 'stop':
        stoped_data = zudilnik.stop_last_record()
        if stoped_data:
            vprint('Stoped record #{} started at {}, duration {}'.format(
                stoped_data['last_record_id'], stoped_data['started_at'],
                stoped_data['duration']
            ))

    elif command == 'comment':
        comment = params[0]
        data = zudilnik.comment_last_subproject(comment)
        vprint('Updated comment for record #{} started at {}'.format(
            data['record_id'], data['record_started_at']
        ))

    elif command == 'newgoal' or command == 'ng':
        (project_name, goal_name) = params
        goal_id = zudilnik.add_new_goal(project_name, goal_name)
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
            vprint(goal['name'], time=False)
            if goal['status'] == 'due':
                vprint("DUE {} more before {}".format(
                    goal['duration'], goal['deadline']
                ), time=False)
            else:
                vprint("OVERWORKED goal by {}".format(
                    (goal['duration'],)
                ), time=False)

            vprint(
                "(goal started at {}, hours per day: {}, worked today {}, total {})".format(
                goal['started'], goal['last_hours_per_day'],
                goal['total_worked_today'], goal['total_worked']
            ), time=False)
    
    elif command == 'timelog' or command == 'tl':
        limit = params[0] if len(params) >= 1 else 12
        timelog = zudilnik.get_timelog(limit)
        for day in timelog:
            vprint(day, time=False)
            for row in timelog[day]:
                vprint(' {}-{}: [{}/{}] - {} ({})'.format(
                    row['started_at'], row['stoped_at'], row['project'],
                    row['subproject'], row['comment'], row['duration']
                ), time=False)

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
