from datetime import datetime
from typing import TypeVar
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import aliased
from models import Base
from app_registry import AppRegistry


TProject = TypeVar("TProject", bound="Project")


class Project(Base):
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('projects.id'))
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(Integer, nullable=False)

    __table_args__ = (UniqueConstraint('user_id', 'name'),)

    @classmethod
    def add_new(
        cls, app: AppRegistry, user_id: int, project_name: str
    ) -> int:
        """Create a new project."""
        project = cls(
            name=project_name,
            user_id=user_id,
            created_at=int(datetime.utcnow().timestamp())
        )
        app.session.add(project)
        app.session.commit()
        return project.id

    @classmethod
    def add_new_subproject(
        cls, app: AppRegistry, user_id: int, project_name: str,
        subproject_name: str
    ) -> int:
        """Create a new subproject."""
        project = (
            app.session.query(cls)
            .filter(
                cls.name == project_name,
                cls.user_id == user_id
            )
            .one()
        )
        subproject = cls(
            parent_id=project.id,
            user_id=user_id,
            name=subproject_name,
            created_at=int(datetime.utcnow().timestamp())
        )
        app.session.add(subproject)
        app.session.commit()
        return subproject.id

    @classmethod
    def get_by_id(
        cls, app: AppRegistry, project_id: int
    ) -> TProject:
        return (
            app.session.query(cls)
            .filter(cls.id == project_id)
            .one()
        )

    @classmethod
    def get_by_name(
        cls, app: AppRegistry, user_id: int, project_name: str
    ) -> TProject:
        return (
            app.session.query(cls)
            .filter(cls.name == project_name, cls.user_id == user_id)
            .one()
        )

    @classmethod
    def get_root_projects(
        cls, app: AppRegistry, user_id: int
    ) -> list[TProject]:
        """Get all root projects for a specific user."""
        return (
            app.session.query(cls)
            .filter(
                cls.user_id == user_id,
                cls.parent_id.is_(None)
            )
            .all()
        )

    @classmethod
    def get_subprojects(
        cls, app: AppRegistry, user_id: int, project_name: str
    ) -> list[TProject]:
        """Get all subprojects of a specific project for a specific user."""
        Subproject = aliased(cls)
        return (
            app.session.query(Subproject)
            .join(cls, Subproject.parent_id == cls.id)
            .filter(
                cls.user_id == user_id,
                cls.name == project_name,
            )
            .all()
        )

    @classmethod
    def find_by_name(
        cls, app: AppRegistry, user_id: int, pattern: str
    ) -> list[str]:
        """Find projects by pattern for a specific user."""
        projects = (
            app.session.query(cls.name)
            .filter(
                cls.name.like(pattern + "%"),
                cls.user_id == user_id,
            )
            .all()
        )
        return [project[0] for project in projects]

    @classmethod
    def find_root_projects(
        cls, app: AppRegistry, user_id: int, pattern: str
    ) -> list[str]:
        """Find root projects by pattern for a specific user."""
        projects = (
            app.session.query(cls.name)
            .filter(
                cls.name.like(pattern + "%"),
                cls.parent_id.is_(None),
                cls.user_id == user_id,
            )
            .all()
        )
        return [project[0] for project in projects]
