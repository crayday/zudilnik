from datetime import datetime, date, time, timedelta
from enum import Enum
from typing import TypeVar
from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    UniqueConstraint,
    Enum as SQLAlchemyEnum,
)
from models import Base, Project
from app_registry import AppRegistry


TGoal = TypeVar("TGoal", bound="Goal")


class GoalType(Enum):
    HOURS_LIGHT = 'hours_light'
    HOURS_MANDATORY = 'hours_mandatory'


GoalTypeEnum = SQLAlchemyEnum(GoalType)


class Goal(Base):
    __tablename__ = 'goals'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    project_id = Column(Integer, ForeignKey('projects.id'))
    name = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)
    archived_at = Column(Integer)
    type = Column(GoalTypeEnum, nullable=False, default=GoalType.HOURS_LIGHT)

    __table_args__ = (UniqueConstraint('user_id', 'name'),)

    @classmethod
    def add_new(
        cls,
        app: AppRegistry,
        user_id: int,
        project_name: str,
        goal_name: str,
        goal_type: GoalType = GoalType.HOURS_LIGHT
    ) -> int:
        project = Project.get_by_name(app, user_id, project_name)

        goal = cls(
            user_id=user_id,
            project_id=project.id,
            name=goal_name,
            type=goal_type,
            created_at=int(datetime.utcnow().timestamp())
        )

        app.session.add(goal)
        app.session.commit()
        return goal.id

    @classmethod
    def get_by_name(
        cls, app: AppRegistry, user_id: int, goal_name: str
    ) -> TGoal:
        """Get goal by name for a specific user."""
        return (
            app.session.query(cls)
            .filter(
                cls.name == goal_name,
                cls.user_id == user_id,
            )
            .one()
        )

    @classmethod
    def find_by_name(
        cls, app: AppRegistry, user_id: int, pattern: str
    ) -> list[str]:
        """Find goals by pattern for a specific user."""
        goals = (
            app.session.query(cls.name)
            .filter(
                cls.name.like(pattern + "%"),
                cls.user_id == user_id,
            )
            .all()
        )
        return [goal[0] for goal in goals]

    @classmethod
    def set_type_by_name(
        cls, app: AppRegistry,
        user_id: int,
        goal_name: str,
        goal_type: GoalType
    ) -> None:
        """Set the type of a goal by its name for a specific user."""
        affected_rows = (
            app.session.query(cls)
            .filter(
                cls.name == goal_name,
                cls.user_id == user_id,
            )
            .update({cls.type: goal_type})
        )
        app.session.commit()

        if affected_rows == 0:
            raise ValueError(
                "No goal was found with the provided user_id and goal_name.")

    @classmethod
    def archive_by_name(
        cls, app: AppRegistry, user_id: int, goal_name: str
    ) -> None:
        """
        Archive a goal by setting the archived_at field to the current
        timestamp.
        """
        affected_rows = (
            app.session.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.name == goal_name
            )
            .update({cls.archived_at: int(datetime.utcnow().timestamp())})
        )

        app.session.commit()

        if affected_rows == 0:
            raise ValueError(
                "No goal was found with the provided user_id and goal_name.")
