from datetime import datetime, timedelta, time as dttime, date as dtdate
from time import time
import re

class Zudilnik:
    def __init__(self, cur, deadline):
        self.cur = cur
        self.deadline = deadline # last sec. of commitment day before deadline
                                 # (NOT first sec. of day after deadline)

    def is_deadline_before_noon(self):
        return self.deadline < dttime(12)

    def add_new_project(self, project_name):
        self.cur.execute("""
        INSERT INTO projects (name, created_at) VALUES (?,?)
        """, (project_name, int(time())))
        self.cur.execute('SELECT LAST_INSERT_ROWID()')
        (project_id,) = self.cur.fetchone()
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
        return subproject_id

    def get_last_time_record(self):
        self.cur.execute("""
        SELECT * FROM timelog ORDER BY id DESC LIMIT 1
        """)
        return self.cur.fetchone()

    def stop_last_record(self, subproject_id_to_start=None):
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
            self.cur.execute('SELECT id, name FROM subprojects WHERE name = ?', (subproject_name,))
            not_found_error = "subproject "+subproject_name+" not found"
        else:
            self.cur.execute("""
            SELECT s.id, s.name
            FROM timelog t
                JOIN subprojects s ON s.id = t.subproject_id
            ORDER BY t.id DESC LIMIT 1
            """)
            not_found_error = "No subprojects with timelog records at all"
        subproject = self.cur.fetchone()
        if not subproject:
            raise Exception(not_found_error)

        dont_stop_subproject_id = None if restart_anyway else subproject['id']
        stoped_data = self.stop_last_record(dont_stop_subproject_id)

        # now insert new record
        self.cur.execute("""
            INSERT INTO timelog (subproject_id, started_at, comment)
            VALUES (?, ?, ?)
        """, (subproject['id'], int(time()), comment))

        return {
            "stoped_last_record": stoped_data,
            "subproject": subproject,
        }

    def comment_last_record(self, comment):
        last_time_record = self.get_last_time_record()
        if not last_time_record:
            raise Exception("No time records at all")
        return self.comment_record(last_time_record['id'], comment)

    def comment_record(self, record_id, comment):
        self.cur.execute("""
        SELECT * FROM timelog WHERE id = ?
        """, (record_id,))
        record = self.cur.fetchone()
        if not record:
            raise Exception("Timelog record {} is not found".format(record_id))
        self.cur.execute("""
        UPDATE timelog SET comment = ? WHERE id = ?
        """, (comment, record_id))
        started_at_dt = datetime.fromtimestamp(record['started_at'])
        return {
            'record_id': record_id,
            'record_started_at': started_at_dt.strftime('%F %T'),
        }

    def delete_last_record(self):
        last_time_record = self.get_last_time_record()
        if not last_time_record:
            raise Exception("No time records at all")
        return self.delete_record(last_time_record['id'])

    def delete_record(self, record_id):
        self.cur.execute("""
        SELECT id FROM timelog WHERE id = ?
        """, (record_id,))
        record = self.cur.fetchone()
        if not record:
            raise Exception("Timelog record {} is not found".format(record_id))
        self.cur.execute("""
        DELETE FROM timelog WHERE id = ? 
        """, (record_id,))
        return {
            'record_id': record_id,
        }

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
        return goal_id

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
        startofday_dt = endofday_dt - timedelta(days=1)
        
        # get list of goal's subprojects
        if goal['subproject_id']:
            subproject_ids = [goal['subproject_id']]
        else:
            self.cur.execute("""
            SELECT id FROM subprojects WHERE project_id = ?
            """, (goal['project_id'],))
            subproject_ids = [row['id'] for row in self.cur]

        # first calculate how much hours already worked
        self.cur.execute("""
        SELECT SUM(duration) AS sum,
            SUM(CASE WHEN started_at > ? THEN duration ELSE 0 END) AS sum_today
        FROM timelog
        WHERE subproject_id IN ("""+','.join(['?']*len(subproject_ids))+""")
            AND started_at > ?
            AND started_at <= ?
        """, (startofday_dt.timestamp(), *subproject_ids, goal_started_dt.timestamp(), endofday_dt.timestamp()))
        worked_data = self.cur.fetchone()
        seconds_worked = worked_data['sum']
        seconds_worked_today = worked_data['sum_today']
        if not seconds_worked:
            seconds_worked = 0
        if not seconds_worked_today:
            seconds_worked_today = 0

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
