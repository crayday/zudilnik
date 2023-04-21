from datetime import datetime
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app_registry import AppRegistry
from config import Config
from models import Base, User, Project


@pytest.fixture(scope='module')
def app() -> AppRegistry:
    config = Config()
    config.database_uri = 'sqlite:///:memory:'
    engine = create_engine(config.database_uri, future=True)
    with engine.connect() as con:
        con.execute(text("PRAGMA foreign_keys = ON;"))
    Base.metadata.create_all(engine)
    session = Session(engine)
    now = lambda: datetime.fromtimestamp(0)  # 1970-01-01
    return AppRegistry(config, session, now)


@pytest.fixture(scope='module')
def user_id(app: AppRegistry) -> int:
    user = User(id=1, name='Test User')
    app.session.add(user)
    app.session.commit()
    return user.id


def test_add_new(app: AppRegistry, user_id: int) -> None:
    project_name = "Test Project"
    project_id = Project.add_new(app, user_id, project_name)
    assert project_id > 0
    project = Project.get_by_id(app, project_id)
    assert project.name == project_name
    assert project.user_id == user_id


def test_add_new_subproject(app: AppRegistry, user_id: int) -> None:
    project_name = "Test Parent Project"
    subproject_name = "Test Subproject"
    parent_project_id = Project.add_new(app, user_id, project_name)
    subproject_id = Project.add_new_subproject(
        app, user_id, project_name, subproject_name
    )
    subproject = Project.get_by_id(app, subproject_id)
    assert subproject.parent_id == parent_project_id
    assert subproject.name == subproject_name
    assert subproject.user_id == user_id


def test_get_by_id(app: AppRegistry, user_id: int) -> None:
    project_name = "Test Project 2"
    project_id = Project.add_new(app, user_id, project_name)
    project = Project.get_by_id(app, project_id)
    assert project.name == project_name
    assert project.user_id == user_id


def test_get_by_name(app: AppRegistry, user_id: int) -> None:
    project_name = "Test Project 3"
    project_id = Project.add_new(app, user_id, project_name)
    project = Project.get_by_name(app, user_id, project_name)
    assert project.id == project_id
    assert project.name == project_name
    assert project.user_id == user_id


def test_get_root_projects(app: AppRegistry, user_id: int) -> None:
    user_id = 1
    project_name1 = "Test Root Project 1"
    project_name2 = "Test Root Project 2"
    Project.add_new(app, user_id, project_name1)
    Project.add_new(app, user_id, project_name2)
    root_projects = Project.get_root_projects(app, user_id)
    project_names = [project.name for project in root_projects]
    assert project_name1 in project_names
    assert project_name2 in project_names


def test_get_subprojects(app: AppRegistry, user_id: int) -> None:
    project_name = "Test Parent Project 2"
    subproject_name1 = "Test Subproject 1"
    subproject_name2 = "Test Subproject 2"
    Project.add_new(app, user_id, project_name)
    Project.add_new_subproject(
        app, user_id, project_name, subproject_name1
    )
    Project.add_new_subproject(
        app, user_id, project_name, subproject_name2
    )
    subprojects = Project.get_subprojects(app, user_id, project_name)
    subproject_names = [subproject.name for subproject in subprojects]
    assert subproject_name1 in subproject_names
    assert subproject_name2 in subproject_names


def test_find_by_name(app: AppRegistry, user_id: int) -> None:
    project_name1 = "Test Find Project 1"
    project_name2 = "Test Find Project 2"
    Project.add_new(app, user_id, project_name1)
    Project.add_new(app, user_id, project_name2)
    found_projects = Project.find_by_name(app, user_id, "Test Find")
    assert project_name1 in found_projects
    assert project_name2 in found_projects


def test_find_root_projects(app: AppRegistry, user_id: int) -> None:
    user_id = 1
    root_project_name1 = "Test Find Root Project 1"
    root_project_name2 = "Test Find Root Project 2"
    subproject_name = "Test Find Subproject"
    Project.add_new(app, user_id, root_project_name1)
    Project.add_new(app, user_id, root_project_name2)
    Project.add_new_subproject(
        app, user_id, root_project_name1, subproject_name
    )
    found_projects = Project.find_root_projects(
        app, user_id, "Test Find Root"
    )
    assert root_project_name1 in found_projects
    assert root_project_name2 in found_projects
    assert subproject_name not in found_projects
