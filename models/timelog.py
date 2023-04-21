import re
from typing import TypeVar
from dataclasses import dataclass
from sqlalchemy import Column, Integer, String, ForeignKey
from models import Base, Project
from .helper import datetime_from_string
from app_registry import AppRegistry


TTimeLog = TypeVar("TTimeLog", bound="TimeLog")


@dataclass
class StartProjectData:
    started_project: Project
    stoped_record: TTimeLog


class TimeLog(Base):
    __tablename__ = 'timelog'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    started_at = Column(Integer, nullable=False)
    stoped_at = Column(Integer)
    duration = Column(Integer)
    comment = Column(String)

    @classmethod
    def get_last_time_record(
        cls, app: AppRegistry, user_id: int, tail_number: int = 1
    ) -> TTimeLog:
        """
        Get the last time record for the specified user.
        The optional tail_number parameter represents the position of
        the record in the list of time records when sorted by start time
        in descending order.
        """
        return (
            app.session.query(cls)
            .filter(cls.user_id == user_id)
            .order_by(cls.started_at.desc(), cls.id.desc())
            .offset(tail_number - 1)
            .first()
        )

    @classmethod
    def stop_last_record(
        cls,
        app: AppRegistry,
        user_id: int,
        commit: bool = True
    ) -> TTimeLog:
        last_time_record = cls.get_last_time_record(app, user_id)

        # Return if last time record is non existent or is already stoped
        if not last_time_record or last_time_record.stoped_at:
            return None

        last_time_record.stop(app, commit=commit)
        return last_time_record

    @classmethod
    def start_project(
        cls,
        app: AppRegistry,
        user_id: int,
        project_name: str = None,
        comment: str = None,
        restart_anyway: bool = False
    ) -> StartProjectData:
        """
        Start working on a project.
        If a project is currently running, stop it first.
        If no project name is provided, the last active project
        will be started.
        """
        last_time_record = cls.get_last_time_record(app, user_id)

        # Find the project to start
        if project_name:
            project_to_start = Project.get_by_name(app, user_id, project_name)
        else:
            if not last_time_record:
                raise ValueError("No projects with timelog records yet")
            project_to_start = Project.get_by_id(
                app, last_time_record.project_id)

        # Stop the last timelog record if needed
        time_record_to_stop = None
        if (
            last_time_record
            and (
                last_time_record.project_id != project_to_start.id
                or restart_anyway
            )
        ):
            time_record_to_stop = last_time_record
            time_record_to_stop.stop(app)

        # Insert a new timelog record
        new_time_record = cls(
            user_id=user_id,
            project_id=project_to_start.id,
            started_at=int(app.now().timestamp()),
            comment=comment
        )
        app.session.add(new_time_record)
        app.session.commit()

        return StartProjectData(project_to_start, time_record_to_stop)

    @classmethod
    def get_record(
        cls, app: AppRegistry, user_id: int, record_identifier: str
    ) -> TTimeLog:
        """
        Resolve the record identifier to a time record.
        The record_identifier can be
        1) a string containing 'last', 'penult', 'penpenult' (and so on)
        2) a negative number, which represents the position of the record
           in the log in the reverse order
        3) actual timelog record ID.

        Usage:
            # Get the second to last time record
            TimeLog.resolve_record(app, user_id, "penult")
            TimeLog.resolve_record(app, user_id, -2)
            # Get by actual id number
            TimeLog.resolve_record(app, user_id, "123")
        """
        tail_number = None
        if re.fullmatch(r'((pen)+)ult', record_identifier):
            matches = re.findall(r'pen', record_identifier)
            tail_number = 1 + len(matches)
        elif record_identifier == 'last':
            tail_number = 1
        elif re.fullmatch(r'-\d+', record_identifier):
            tail_number = abs(int(record_identifier))

        if tail_number:
            record = cls.get_last_time_record(app, user_id, tail_number)
            if not record:
                raise ValueError("No time records at all")
        else:
            record_id = int(record_identifier)
            record = (
                app.session.query(cls)
                .filter(cls.id == record_id, cls.user_id == user_id)
                .one()
            )

        return record

    @classmethod
    def comment_record(
        cls,
        app: AppRegistry,
        user_id: int,
        record_identifier: str,
        comment: str
    ) -> TTimeLog:
        """
        Add or update a comment for the specified time record.

        Example:
        updated_record = TimeLog.comment_record(app, user_id, "new comment")
        """
        record = cls.get_record(app, user_id, record_identifier)
        record.comment = comment
        app.session.commit()

        return record

    @classmethod
    def delete_record(
        cls, app: AppRegistry, user_id: int, record_identifier: str
    ) -> TTimeLog:
        """
        Delete the specified time record.

        Example:
        deleted_record = TimeLog.delete_record(app, user_id, "last")
        """
        record = cls.get_record(app, user_id, record_identifier)
        app.session.delete(record)
        app.session.commit()
        return record

    @classmethod
    def set_record_start_time(
        cls, app: AppRegistry,
        user_id: int,
        record_identifier: str,
        time_str: str,
    ) -> TTimeLog:
        """
        Set the start time for the specified time record.

        Example:
        updated_record = TimeLog.set_record_start_time(
            app, user_id, "last", "14:30"
        )
        """
        record = cls.get_record(app, user_id, record_identifier)
        started_at_dt = datetime_from_string(app, time_str)

        if started_at_dt and record.stoped_at:
            duration = record.stoped_at - int(started_at_dt.timestamp())
        else:
            duration = None

        record.started_at = int(started_at_dt.timestamp())
        record.duration = duration
        app.session.commit()

        return record

    @classmethod
    def set_record_stop_time(
        cls,
        app: AppRegistry,
        user_id: int,
        record_identifier: str,
        time_str: str
    ) -> TTimeLog:
        """
        Set the stop time for the specified time record.

        Example:
        updated_record = TimeLog.set_record_stop_time(
            app, user_id, "last", "14:30"
        )
        """
        record = cls.get_record(app, user_id, record_identifier)
        stopped_at_dt = datetime_from_string(app, time_str)
        if record.started_at and stopped_at_dt:
            duration = (
                int(stopped_at_dt.timestamp()) - record.started_at
            )
        else:
            duration = None

        record.stoped_at = int(stopped_at_dt.timestamp())
        record.duration = duration
        app.session.commit()

        return record

    @classmethod
    def set_record_project(
        cls,
        app: AppRegistry,
        user_id: int,
        record_identifier: str,
        project_name: str
    ) -> TTimeLog:
        """
        Assign a project to the specified time record.

        Example:
        updated_record = TimeLog.set_record_project(
            app, user_id, "last", "project_name"
        )
        """
        record = cls.get_record(app, user_id, record_identifier)
        project = Project.get_by_name(app, user_id, project_name)

        record.project_id = project.id
        app.session.commit()

        return record

    def stop(self, app: AppRegistry, commit: bool = True) -> None:
        now = int(app.now().timestamp())
        self.stoped_at = now
        self.duration = now - self.started_at
        if commit:
            app.session.commit()

    @classmethod
    def get_timelog(
        cls, app: AppRegistry, user_id: int, page: int = 1, page_size: int = 10
    ) -> list[tuple[TTimeLog, Project]]:
        """
        Retrieve the timelog along with the associated projects
            for the given user.

        Example:
        timelog = TimeLog.get_timelog(app, user_id, page=1, page_size=10)
        for record, project in timelog:
            print(record.comment)
            print(project.name)
        """
        offset = (page - 1) * page_size
        return (
            app.session.query(cls, Project)
            .join(Project, cls.project_id == Project.id)
            .filter(cls.user_id == user_id)
            .order_by(cls.started_at.desc(), cls.id.desc())
            .offset(offset)
            .limit(page_size)
            .all()
        )
