from datetime import datetime, timedelta, time as dttime, date as dtdate
from time import time
import re
import sqlite3

class Zudilnik:
    def __init__(self, deadline, dbpath):
        self.deadline = deadline # last sec. of commitment day before deadline
                                 # (NOT first sec. of day after deadline)
        self.con = sqlite3.connect(dbpath)
        self.con.row_factory = sqlite3.Row
        self.cur = self.con.cursor()

    def is_deadline_before_noon(self):
        return self.deadline < dttime(12)

    def add_new_project(self, project_name):
        self.cur.execute("""
        INSERT INTO projects (name, created_at) VALUES (?,?)
        """, (project_name, int(time())))
        self.cur.execute('SELECT LAST_INSERT_ROWID()')
        (project_id,) = self.cur.fetchone()
        self.con.commit()
        return project_id

    def add_new_subproject(self, project_name, subproject_name):
        self.cur.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
        project = self.cur.fetchone()
        if not project:
            raise Exception("project "+project_name+" not found")
        self.cur.execute("""
        INSERT INTO subprojects (project_id, name, created_at) VALUES (?,?,?)
        """, (project['id'], subproject_name, int(time())))
        self.cur.execute('SELECT LAST_INSERT_ROWID()')
        (subproject_id,) = self.cur.fetchone()
        self.con.commit()
        return subproject_id

    def get_last_time_record(self, tail_number=1):
        self.cur.execute("""
        SELECT * FROM timelog ORDER BY started_at DESC, id DESC LIMIT 1 OFFSET ?
        """, (tail_number-1,))
        return self.cur.fetchone()

    def stop_last_record(self, subproject_id_to_start=None, commit=True):
        last_time_record = self.get_last_time_record()

        # check if last time record was stopped. If not - stop it
        if last_time_record and not last_time_record['stoped_at']:
            if subproject_id_to_start and last_time_record['subproject_id'] == subproject_id_to_start:
                raise Exception("subproject #{} already started".format(subproject_id_to_start))
            now = int(time())
            started_at_dt = datetime.fromtimestamp(last_time_record['started_at'])
            duration = now - last_time_record['started_at']
            self.cur.execute("""
            UPDATE timelog SET stoped_at = ?, duration = ? WHERE id = ?
            """, (now, duration, last_time_record['id']))
            if commit:
                self.con.commit()

            return {
                "last_record_id": last_time_record['id'],
                "started_at": started_at_dt.strftime('%F %T'),
                "duration": seconds_to_hms(duration),
            }
        else:
            return None
    
    def start_subproject(self, subproject_name=None, comment=None, restart_anyway=False):
        # fist find subproject to start
        if subproject_name:
            subproject = self.get_project(subproject_name)
        else:
            self.cur.execute("""
                SELECT s.id, s.name
                FROM timelog t
                    JOIN subprojects s ON s.id = t.subproject_id
                ORDER BY t.id DESC LIMIT 1
            """)
            subproject = self.cur.fetchone()
            if not subproject:
                raise Exception("No subprojects with timelog records at all")

        dont_stop_subproject_id = None if restart_anyway else subproject['id']
        stoped_data = self.stop_last_record(dont_stop_subproject_id, commit=False)

        # now insert new record
        self.cur.execute("""
            INSERT INTO timelog (subproject_id, started_at, comment)
            VALUES (?, ?, ?)
        """, (subproject['id'], int(time()), comment))
        self.con.commit()

        return {
            "stoped_last_record": stoped_data,
            "subproject": subproject,
        }

    def comment_record(self, record_identifier, comment):
        record_id = self.get_record_id(record_identifier)
        record = self.verify_record(record_id)
        self.cur.execute("""
        UPDATE timelog SET comment = ? WHERE id = ?
        """, (comment, record['id']))
        self.con.commit()
        started_at_dt = datetime.fromtimestamp(record['started_at'])
        return {
            'record_id': record['id'],
            'record_started_at': started_at_dt.strftime('%F %T'),
        }

    def delete_record(self, record_identifier):
        record_id = self.get_record_id(record_identifier)
        self.verify_record(record_id)
        self.cur.execute("""
        DELETE FROM timelog WHERE id = ? 
        """, (record_id,))
        self.con.commit()
        return {
            'record_id': record_id,
        }

    def set_record_start_time(self, record_identifier, time_str):
        record_id = self.get_record_id(record_identifier)
        record = self.verify_record(record_id)
        started_at_dt = datetime_from_string(time_str)
        if started_at_dt and record['stoped_at']:
            duration = record['stoped_at'] - started_at_dt.timestamp()
        else:
            duration = None
        self.cur.execute("""
        UPDATE timelog SET started_at = ?, duration = ? WHERE id = ? 
        """, (started_at_dt.timestamp(), duration, record_id))
        self.con.commit()

        return {
            'record_id': record_id,
            'started_at': started_at_dt.strftime('%F %T'),
            'duration': seconds_to_hms(duration) if duration else None,
        }

    def set_record_stop_time(self, record_identifier, time_str):
        record_id = self.get_record_id(record_identifier)
        record = self.verify_record(record_id)
        stoped_at_dt = datetime_from_string(time_str)
        if record['started_at'] and stoped_at_dt:
            duration = stoped_at_dt.timestamp() - record['started_at']
        else:
            duration = None
        self.cur.execute("""
        UPDATE timelog SET stoped_at = ?, duration = ? WHERE id = ? 
        """, (stoped_at_dt.timestamp(), duration, record_id))
        self.con.commit()

        return {
            'record_id': record_id,
            'stoped_at': stoped_at_dt.strftime('%F %T'),
            'duration': seconds_to_hms(duration),
        }

    def set_record_project(self, record_identifier, project_name):
        record_id = self.get_record_id(record_identifier)
        self.verify_record(record_id)
        project = self.get_project(project_name)
        self.cur.execute("""
        UPDATE timelog SET subproject_id = ? WHERE id = ? 
        """, (project['id'], record_id))
        self.con.commit()
        return {
            'record_id': record_id,
        }

    def get_project(self, project_name):
        self.cur.execute('SELECT * FROM subprojects WHERE name = ?', (project_name,))
        project = self.cur.fetchone()
        if not project:
            raise Exception("project "+project_name+" not found")
        return project

    def find_root_projects(self, pattern):
        self.cur.execute("""
            SELECT name
            FROM projects
            WHERE name like ?
        """, (pattern+'%',))
        names = []
        projects = self.cur.fetchall()
        return [project["name"] for project in projects]

    def find_projects(self, pattern):
        self.cur.execute("""
            SELECT name
            FROM subprojects
            WHERE name like ?
        """, (pattern+'%',))
        names = []
        subprojects = self.cur.fetchall()
        return [subproject["name"] for subproject in subprojects]

    def find_projects2(self, pattern):
        subprojects = self.find_projects(pattern)
        if not subprojects:
            return self.find_root_projects(pattern)
        else:
            return subprojects


    def find_goals(self, pattern):
        self.cur.execute("""
            SELECT name
            FROM goals
            WHERE name like ?
        """, (pattern+'%',))
        names = []
        goals = self.cur.fetchall()
        return [goal["name"] for goal in goals]

    def verify_record(self, record_id):
        self.cur.execute("""
        SELECT * FROM timelog WHERE id = ?
        """, (record_id,))
        record = self.cur.fetchone()
        if not record:
            raise Exception("Timelog record {} is not found".format(record_id))
        return record

    def add_new_goal(self, project_name, goal_name, goal_type='hours_light'):
        # first try to search for subproject with given name
        self.cur.execute("""
            SELECT id, project_id FROM subprojects WHERE name = ? 
        """, (project_name,))
        subproject = self.cur.fetchone()
        if subproject:
            project_id = subproject['project_id']
            subproject_id = subproject['id']
        else:
            # next try to search for project with given name
            self.cur.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
            project = self.cur.fetchone()
            if project:
                project_id = project['id']
                subproject_id = None
            else:
                raise Exception("project {} not found".format(project_name))
        self.cur.execute("""
            INSERT INTO goals (project_id, subproject_id, name, type, created_at)
            VALUES (?,?,?,?,STRFTIME('%s','now'))
        """, (project_id, subproject_id, goal_name, goal_type))
        self.cur.execute('SELECT LAST_INSERT_ROWID()')
        (goal_id,) = self.cur.fetchone()
        self.con.commit()
        return goal_id

    def set_goal_type(self, goal_name, goal_type):
        self.cur.execute("""
            UPDATE goals SET type = ? WHERE name = ?
        """, (goal_type, goal_name))
        self.con.commit()

    def archive_goal(self, goal_name):
        self.cur.execute("""
            UPDATE goals SET archived_at = STRFTIME('%s','now') WHERE name = ?
        """, (goal_name,))
        self.con.commit()

    def get_commitment_date(self, dt):
        commitment_date = dt.date()
        if self.is_deadline_before_noon():
            commitment_date -= timedelta(days=1)
        if dt.time() > self.deadline:
            commitment_date += timedelta(days=1)
        return commitment_date

    # get_commitment: returns day commitments in order of freshness
    def get_commitments_by_date(self, goal_id, day):
        day_str = day.isoformat()
        self.cur.execute("""
            SELECT *
            FROM hoursperday
            WHERE goal_id = ?
                AND weekday = ?
                AND date_from <= ?
                AND (date_to IS NULL OR date_to >= ?)
            ORDER BY date_from DESC
        """, (goal_id, day.isoweekday(), day_str, day_str))
        return self.cur.fetchall()

    def get_goal_info(self, goal_id):
        # get goal
        self.cur.execute("""
            SELECT * FROM goals WHERE id = ?
        """, (goal_id,))
        goal = self.cur.fetchone()
        if not goal:
            raise Exception("Goal #{} not found".format(goal_id))

        # get goal start time
        goal_created_dt = datetime.fromtimestamp(goal['created_at'])
        goal_started_dt = datetime.combine(goal_created_dt.date(), self.deadline)
        # if goal was created before deadline, then goal start time is in previous day
        if goal_created_dt.time() < self.deadline:
            goal_started_dt -= timedelta(days=1)

        # get start & end of the day
        now = datetime.now()
        endofday_dt = datetime.combine(now.date(), self.deadline)
        if now.time() > self.deadline:
            endofday_dt += timedelta(days=1)

        # first calculate how much hours already worked
        seconds_worked, seconds_worked_today = self.worked_on_goal(goal, goal_started_dt, endofday_dt, calculate_last_day = True)

        # then calculate how much work should be done by the end of the day
        total_hours_due = 0
        last_hours_per_day = 0
        current_commitment_date = self.get_commitment_date(now)

        if goal['type'] == 'hours_mandatory':
            day = self.get_commitment_date(goal_created_dt)
        else: # hours_light
            day = current_commitment_date

        while day <= current_commitment_date:
            commitments = self.get_commitments_by_date(goal['id'], day)
            if commitments:
                hours_due = commitments[0]['hours']
                total_hours_due += hours_due
            else:
                hours_due = 0
            last_hours_per_day = hours_due
            day += timedelta(days=1)
	
        total_seconds_due = 3600 * total_hours_due

        if goal['type'] == 'hours_mandatory':
            left_seconds_due = total_seconds_due - seconds_worked
        else: # hours_light
            left_seconds_due = total_seconds_due - seconds_worked_today

        if left_seconds_due >= 0:
            status = 'due'
            duration_str = seconds_to_hms(left_seconds_due)
        else:
            status = 'overworked'
            duration_str = seconds_to_hms(-left_seconds_due)

        return {
            "name": goal['name'],
            "status": status,
            "duration": duration_str,
            "deadline": endofday_dt.strftime('%F %T'),
            "started": goal_started_dt.strftime('%F'),
            "last_hours_per_day": last_hours_per_day,
            "total_worked": seconds_to_hms(seconds_worked),
            "total_worked_today": seconds_to_hms(seconds_worked_today),
            "total_seconds_due": seconds_to_hms(total_seconds_due),
        }

    def worked_on_goal2(self, goal_name, from_date, to_date=None):
        self.cur.execute('SELECT * FROM goals WHERE name = ?', (goal_name,))
        goal = self.cur.fetchone()
        if not goal:
            raise Exception(f"goal '{goal_name}' not found")
        from_dt, to_dt = dates_range_from_strings(from_date, to_date, self.deadline)
        seconds_worked = self.worked_on_goal(goal, from_dt, to_dt)
        return seconds_to_hms(seconds_worked), from_dt, to_dt

    def worked_on_goal(self, goal, from_dt, to_dt, calculate_last_day = False):
        # get list of goal's subprojects
        if goal['subproject_id']:
            subproject_ids = [goal['subproject_id']]
        else:
            self.cur.execute("""
                SELECT id FROM subprojects WHERE project_id = ?
            """, (goal['project_id'],))
            subproject_ids = [row['id'] for row in self.cur]

        return self.worked_on_subprojects(subproject_ids, from_dt, to_dt, calculate_last_day)

    def worked_on_project(self, project_name, from_date, to_date=None):
        try:
            project = self.get_project(project_name)
            subproject_ids = [ project['id'] ]
        except (Exception):
            projects = self.get_subprojects(project_name)
            subproject_ids = [row['id'] for row in projects]
            
        from_dt, to_dt = dates_range_from_strings(from_date, to_date, self.deadline)
        seconds_worked = self.worked_on_subprojects(subproject_ids, from_dt, to_dt)
        return seconds_to_hms(seconds_worked), from_dt, to_dt

    def worked_on_subprojects(self, subproject_ids, from_dt, to_dt, calculate_last_day = False):
        startofday_dt = to_dt - timedelta(days=1)

        # calculate how much hours worked
        fields, params = [], []
        if calculate_last_day:
            fields.append("SUM(CASE WHEN started_at > ? THEN duration ELSE 0 END) AS sum_last_day")
            params.append(startofday_dt.timestamp())
        else:
            select_worked_last_day = ""

        fields_str = ''.join([f+', ' for f in fields])
        placeholder_str = ','.join(['?']*len(subproject_ids))
        self.cur.execute(f"""
            SELECT {fields_str}
                SUM(duration) AS sum
            FROM timelog
            WHERE subproject_id IN ({placeholder_str})
                AND started_at > ?
                AND started_at <= ?
        """, (*params, *subproject_ids, from_dt.timestamp(), to_dt.timestamp()))

        worked_data = self.cur.fetchone()
        seconds_worked = worked_data['sum']
        if calculate_last_day:
            seconds_worked_last_day = worked_data['sum_last_day']
            if not seconds_worked_last_day:
                seconds_worked_last_day = 0

        if not seconds_worked:
            seconds_worked = 0

        if calculate_last_day:
            return seconds_worked, seconds_worked_last_day
        else:
            return seconds_worked

    def get_goals_info(self):
        self.cur.execute("""
            SELECT id
            FROM goals
            WHERE archived_at IS NULL
        """)
        goals_info = []
        for goal in self.cur.fetchall():
            goal_info = self.get_goal_info(goal['id'])
            if goal_info['total_seconds_due'] != '0':
                goals_info.append(goal_info)

        return goals_info

    def set_hours_per_day(self, goal_name, hours, weekday_filter = None):
        if not weekday_filter:
            weekday_filter = '1-7'

        # get weekday numbers from weekday filter
        weekdays = []
        intervals = weekday_filter.split(',')
        for interval in intervals:
            match = re.match(r'([1-7])-([1-7])$', interval)
            if match:
                from_day = int(match.group(1))
                to_day = int(match.group(2))
                for day in range(from_day, to_day+1):
                    weekdays.append(day)
            elif re.match(r'[1-7]$', interval):
                weekdays.append(int(interval))
            else:
                raise Exception("invalid weekday filter '{}'".format(weekday_filter))

        # find goal id
        self.cur.execute('SELECT * FROM goals WHERE name = ?', (goal_name,))
        goal = self.cur.fetchone()
        if not goal:
            raise Exception("goal '{}' not found".format(goal_name))

        # find out day of commitment
        commitment_date = self.get_commitment_date(datetime.now())

        # find out current active commitments for same weekdays
        commitment_date_str = commitment_date.isoformat()
        self.cur.execute("""
            SELECT *
            FROM hoursperday
            WHERE goal_id = ?
                AND weekday IN ("""+','.join(['?']*len(weekdays))+""")
                AND date_from <= ?
                AND (date_to IS NULL OR date_to >= ?)
            ORDER BY date_from DESC
        """, (goal['id'], *weekdays, commitment_date_str, commitment_date_str))
        commitments = self.cur.fetchall()

        day_before = commitment_date - timedelta(days=1)
        day_before_str = day_before.isoformat()
        for prev_commitment in commitments:
            # if previous prev_commitment was not really active any day - remove it
            date_from_d = dtdate(*[int(e) for e in prev_commitment['date_from'].split('-')])
            diff_with_weekday = date_from_d.isoweekday() - prev_commitment['weekday']
            if diff_with_weekday < 0:
                diff_with_weekday += 7
            real_date_from_d = date_from_d + timedelta(days=diff_with_weekday)

            if real_date_from_d >= commitment_date:
                self.cur.execute('DELETE FROM hoursperday WHERE id = ?', (prev_commitment['id'],))
            else: # prev_commitment was active prior to prev_commitment date - unactivate it
                self.cur.execute('UPDATE hoursperday SET date_to = ? WHERE id = ?',
                    (day_before_str, prev_commitment['id'],))

        # commit hours per day to all weekdays separately
        for weekday in weekdays:
            self.cur.execute("""
                INSERT INTO hoursperday (goal_id, weekday, hours, date_from)
                VALUES (?, ?, ?, ?)
            """, (goal['id'], weekday, hours, commitment_date_str))
        self.con.commit()

    def get_timelog(self, limit=10):
        self.cur.execute("""
            SELECT tl.*, sp.name AS subproject_name, p.name AS project_name
            FROM timelog tl
                JOIN subprojects sp ON sp.id = tl.subproject_id
                JOIN projects p ON p.id = sp.project_id
            ORDER BY tl.started_at DESC, tl.id DESC
            LIMIT ?
        """, (limit,))
        timelog = {}
        for row in self.cur:
            started_at_dt = datetime.fromtimestamp(row['started_at'])
            if row['stoped_at']:
                stoped_at_dt = datetime.fromtimestamp(row['stoped_at'])
                stoped_at = stoped_at_dt.time().strftime("%H:%M")
                duration = seconds_to_hms(row['duration'])
            else:
                stoped_at = '.....'
                current_seconds = int(time() - row['started_at'])
                duration = seconds_to_hms(current_seconds)
            day = self.get_commitment_date(started_at_dt).isoformat()
            if day not in timelog:
                timelog[day] = []

            timelog[day].append({
                "id": row['id'],
                "project": row['project_name'],
                "subproject": row['subproject_name'],
                "started_at": started_at_dt.time().strftime("%H:%M"),
                "stoped_at": stoped_at,
                "duration": duration,
                "comment": row['comment'] if row['comment'] else '...'
            })
        return timelog

    def get_projects(self):
        return self.cur.execute("SELECT * FROM projects").fetchall()

    def get_subprojects(self, project_name):
        return self.cur.execute("""
            SELECT sp.*
            FROM projects p
                JOIN subprojects sp ON sp.project_id = p.id
            WHERE p.name = ?
        """, (project_name,)).fetchall()

    def get_record_id(self, record_identifier):
        tail_number = None
        if re.fullmatch(r'((pen)+)ult', record_identifier):
            matches = re.findall(r'pen', record_identifier)
            tail_number = 1+len(matches)
        elif record_identifier == 'last':
            tail_number = 1
        elif re.fullmatch(r'-\d+', record_identifier):
            tail_number = abs(int(record_identifier))

        if tail_number:
            record = self.get_last_time_record(tail_number)
            if not record:
                raise Exception("No time records at all")
            record_id = record['id']
        else:
            record_id = int(record_identifier)

        return record_id

########################### supplementary functions ###########################
def seconds_to_hms(seconds):
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

def datetime_from_string(time_str):
    match = re.match(r'(\d{2}):(\d{2})(?::(\d{2}))?', time_str)
    if match:
        now = datetime.now()
        second = int(match.group(3)) if match.group(3) else 0
        dt = now.replace(hour = int(match.group(1)), minute = int(match.group(2)), second = second)
        if dt > now:
            # Calculated time appeared in future.
            # Certanly time should refer to the previous day not to the future
            return dt - timedelta(days=1)
        else:
            return dt
    match = re.match(r'(\d{4}).(\d{2}).(\d{2}) (\d{2}):(\d{2})(?::(\d{2}))?', time_str)
    if match:
        second = int(match.group(6)) if match.group(6) else 0
        return datetime(
            year = int(match.group(1)),
            month = int(match.group(2)),
            day = int(match.group(3)),
            hour = int(match.group(4)),
            minute = int(match.group(5)),
            second = second)
    raise Exception(f"Doesn't support time string '{time_str}'")

def date_from_string(date_str, default_time=None):
    match = re.match(r'(?:(\d{4}).)?(?:(\d{1,2}).)?(\d{1,2})$', date_str)
    if match:
        today = dtdate.today()
        return datetime(
            year = int(match.group(1)) if match.group(1) else today.year,
            month = int(match.group(2)) if match.group(2) else today.month,
            day = int(match.group(3)),
            hour = default_time.hour,
            minute = default_time.minute,
            second = default_time.second)
    raise Exception(f"Doesn't support date string '{date_str}'")

def dates_range_from_strings(from_date, to_date, default_time=None):
    from_dt = date_from_string(from_date, default_time)
    if to_date:
        to_dt = date_from_string(to_date, default_time) + timedelta(days=1)
    else:
        to_dt = from_dt + timedelta(days=1)
    return from_dt, to_dt
