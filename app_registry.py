from dataclasses import dataclass
from sqlalchemy.orm import Session
from config import Config


@dataclass
class AppRegistry:
    config: Config
    session: Session
