import cmd
from datetime import datetime
from typing import Callable
from app_registry import AppRegistry


class BaseCommand(cmd.Cmd):
    def __init__(
        self, app: AppRegistry, print_fn: Callable = None
    ):
        self.app = app
        self.print_fn = print_fn or print

        self.current_user_id = app.config.cli_user_id
        super().__init__()

    def print(self, message: str) -> None:
        self.print_fn(message)

    def print_w_time(self, message: str) -> None:
        self.print_fn(f"{datetime.now().strftime('%H:%M')}: {message}")
