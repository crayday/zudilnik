from app import db
from sqlalchemy import select, Column, Integer, String, DateTime

class TimeLogRecord(db.model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    project_id = Column(Integer, nullable=False)
    started_at = Column(DateTime, nullable=False)
    stoped_at = Column(DateTime)
    duration = Column(Integer)
    comment = Column(String)

    @classmethod
    def get_last(cls, user):
        sth = select(cls) \
            .where(user_id=user.id) \
            .order_by(cls.started_at.desc(), cls.id.desc()) \
            .limit(1)
        res = db.session.execute(sth)
        return self.cur.fetchone() # FIXME TODO
