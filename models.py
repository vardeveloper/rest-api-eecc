from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Unicode, DateTime

from datetime import datetime
import uuid


Entity = declarative_base()


class Token(Entity):
    __tablename__ = 'tokens'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    def __init__(self, doc_type, doc_number, period):
        self.token = str(uuid.uuid4())
        self.doc_type = doc_type
        self.doc_number = doc_number
        self.period = period

    id = Column(Integer, primary_key=True)
    token = Column(Unicode(36), unique=True, index=True, nullable=False)
    doc_type = Column(Unicode(2), nullable=False)
    doc_number = Column(Unicode(20), nullable=False)
    period = Column(Unicode(6), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


if __name__ == '__main__':
    from sqlalchemy import create_engine

    import settings

    engine = create_engine(
        settings.DATABASE_DSN,
        echo=settings.DEBUG
    )
    Entity.metadata.create_all(engine)
