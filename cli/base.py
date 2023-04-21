import cmd
from typing import Callable
from app_registry import AppRegistry


class BaseCommand(cmd.Cmd):
    def __init__(
        self, app: AppRegistry, print_fn: Callable = None
    ):
        self.app = app
        self.print_fn = print_fn or print

        self.current_user_id = app.config.cli_user_id
        self.prompt = f"{self.app.now().strftime('%H:%M')}> "
        super().__init__()

    def postcmd(self, stop: bool, line: str) -> bool:
        # Update time in the command prompt
        self.prompt = f"{self.app.now().strftime('%H:%M')}> "
        return stop

    def print(self, message: str) -> None:
        self.print_fn(message)

    def print_w_time(self, message: str) -> None:
        self.print_fn(f"{self.app.now().strftime('%H:%M')}: {message}")
