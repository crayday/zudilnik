from sqlalchemy import Column, Integer, String
from models import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)

    def __repr__(self):
        return f'<User #{self.id} {self.name}>'
