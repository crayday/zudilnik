from .helper import cmd_prompt
from .project import ProjectCommand
from .timelog import TimeLogCommand
from .goal import GoalCommand


class ZudilnikCmd(ProjectCommand, TimeLogCommand, GoalCommand):
    prompt = cmd_prompt()

    def postcmd(self, stop: bool, line: str) -> bool:
        # Update time in the command prompt
        self.prompt = cmd_prompt()
        return stop

    def emptyline(self) -> None:
        pass

    def do_EOF(self, line: str) -> bool:
        print()
        return True

    def do_exit(self, line: str) -> bool:
        return True
