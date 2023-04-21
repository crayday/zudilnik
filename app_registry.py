from dataclasses import dataclass
from typing import Callable
from sqlalchemy.orm import Session
from config import Config


@dataclass
class AppRegistry:
    config: Config
    session: Session
    now: Callable[[], int]
