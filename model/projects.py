from app import db
from sqlalchemy import Column, Integer, String, DateTime

class Project(db.model):
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer)
    user_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
