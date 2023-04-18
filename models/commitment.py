from datetime import datetime, date, timedelta
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, or_
from models import Base, Goal
from .helper import parse_weekday_filter, get_day_regarding_deadline
from app_registry import AppRegistry


class Commitment(Base):
    __tablename__ = "hoursperday"

    id = Column(Integer, primary_key=True)
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=False)
    weekday = Column(Integer, nullable=False)  # 1 - monday, 7 - sunday
    hours = Column(Numeric(10, 2), nullable=False)
    date_from = Column(String, nullable=False)  # YYYY-MM-DD
    date_to = Column(String)

    @classmethod
    def _deactivate_previous_commitments(
        cls,
        app: AppRegistry,
        goal: Goal,
        weekdays: list[int],
        commitment_date: date
    ) -> None:
        """
        Deactivate or remove previous commitments for the same weekdays
        before the given commitment date.
        """
        commitment_date_str = commitment_date.isoformat()
        commitments = (
            app.session.query(cls)
            .filter(
                cls.goal_id == goal.id,
                cls.weekday.in_(weekdays),
                cls.date_from <= commitment_date_str,
                or_(
                    cls.date_to.is_(None),
                    cls.date_to >= commitment_date_str
                ),
            )
            .order_by(cls.date_from.desc())
            .all()
        )

        day_before = commitment_date - timedelta(days=1)
        day_before_str = day_before.isoformat()
        for prev_commitment in commitments:
            commitment_start_date = date.fromisoformat(
                prev_commitment.date_from)

            # Calculate the actual start date of the commitment
            # considering its weekday
            diff_with_weekday = (
                commitment_start_date.isoweekday() - prev_commitment.weekday
            )
            if diff_with_weekday < 0:
                diff_with_weekday += 7

            commitment_actual_start_date = (
                commitment_start_date + timedelta(days=diff_with_weekday)
            )

            if commitment_actual_start_date >= commitment_date:
                app.session.delete(prev_commitment)
            else:
                prev_commitment.date_to = day_before_str

    @classmethod
    def _add_new_commitments(
        cls,
        app: AppRegistry,
        goal: Goal,
        hours: float,
        weekdays: list[int],
        commitment_date: date
    ) -> None:
        """
        Commit to work for a given number of hours for a given goal,
        starting from a commitment_date
        """
        commitment_date_str = commitment_date.isoformat()
        for weekday in weekdays:
            new_hours_per_day = cls(
                goal_id=goal.id,
                weekday=weekday,
                hours=hours,
                date_from=commitment_date_str,
            )
            app.session.add(new_hours_per_day)

    @classmethod
    def set_hours_per_day(
        cls,
        app: AppRegistry,
        user_id: int,
        goal_name: str,
        hours: float,
        weekday_filter: str = None,
    ):
        """
        Commit to work for a given number of hours for a given goal on
        days listed in weekday_filter. Deactivate the previous commitments on
        the same days.
        """
        weekdays = parse_weekday_filter(weekday_filter)

        goal = Goal.get_by_name(app, user_id, goal_name)
        if not goal:
            raise ValueError(f"Goal '{goal_name}' was not found")

        commitment_date = get_day_regarding_deadline(
            app.config, datetime.now()
        )
        cls._deactivate_previous_commitments(
            app, goal, weekdays, commitment_date)
        cls._add_new_commitments(app, goal, hours, weekdays, commitment_date)
        app.session.commit()
