from .project import ProjectCommand
from .timelog import TimeLogCommand
from .goal import GoalCommand


class ZudilnikCmd(ProjectCommand, TimeLogCommand, GoalCommand):
    def emptyline(self) -> None:
        pass

    def do_EOF(self, line: str) -> bool:
        print()
        return True

    def do_exit(self, line: str) -> bool:
        return True
