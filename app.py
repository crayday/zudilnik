
import os
from dataclasses import dataclass
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, DeclarativeMeta

@dataclass
class SQLAlchemy:
    model: DeclarativeMeta
    session: Session

db = SQLAlchemy(session=None, model=None)

def init_app(dbpath):
    conn_string = 'sqlite:///'+dbpath
    engine = create_engine(conn_string, future=True)
    db.session = Session(engine)
    db.model = declarative_base()

if __name__ == '__main__':
    init_app()
