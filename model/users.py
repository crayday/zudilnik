from app import db
from sqlalchemy import select, Column, Integer, String

class User(db.model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    
    def __repr__(self):
        return f'<User #{self.id} {self.name}>'
