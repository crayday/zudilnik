from .base import BaseCommand
from .helper import n_params_from_line, get_param_number
from models import Project


class ProjectCommand(BaseCommand):
    def do_np(self, line: str) -> None:
        """shortcut for newproject"""
        self.do_newproject(line)

    def do_newproject(self, line: str) -> None:
        """newproject <project_name> - create a new project with the specified name."""
        (project_name,) = n_params_from_line(line, 1)
        project_id = Project.add_new(
            self.app, self.current_user_id, project_name)
        self.print_w_time(f'Added project "{project_name}" #{project_id}')

    def complete_new(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        """(autocomplete) suggest project names for completion."""
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Project.find_root_projects(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_new(self, line: str) -> None:
        """new <project_name> <subproject_name> - create a new subproject under the specified project."""
        (project_name, subproject_name) = n_params_from_line(line, 2)
        subproject_id = Project.add_new_subproject(
            self.app, self.current_user_id, project_name,
            subproject_name)
        self.print_w_time(
            f'Added subproject "{subproject_name}" #{subproject_id}')

    def complete_ls(self, *args) -> list[str]:
        """autocomplete for a list shortcut"""
        return self.complete_list(*args)

    def do_ls(self, line: str) -> None:
        """shortcut for list"""
        self.do_list(line)

    def complete_list(
        self, text: str, line: str, begidx: int, endidx: int
    ) -> list[str]:
        """(autocomplete) suggest project names for completion."""
        param_number = get_param_number(line, begidx)
        if param_number == 1:
            return Project.find_root_projects(
                self.app, self.current_user_id, text)
        else:
            return []

    def do_list(self, line: str) -> None:
        """list [project_name] - list all subprojects under the specified project or all root projects if no project is specified."""
        (project_name,) = n_params_from_line(line, 1)
        if project_name:
            # concrete project given - need to list all it's subprojects
            projects = Project.get_subprojects(
                self.app, self.current_user_id, project_name)
        else:
            # no project given - need to list all projects
            projects = Project.get_root_projects(
                self.app, self.current_user_id)
        for project in projects:
            self.print(f"#{project.id} {project.name}")
