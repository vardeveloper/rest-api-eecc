from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column,
    Integer,
    Unicode,
    Enum,
    DateTime
)

from datetime import datetime


Entity = declarative_base()


class Log(Entity):
    __tablename__ = 'logs'
    __table_args__ = {
        'mysql_engine': 'InnoDB',
        'mysql_charset': 'utf8'
    }

    id = Column(Integer, primary_key=True)
    channel = Column(Unicode(100), nullable=False)
    action = Column(Enum('view', 'email'), nullable=False)
    template = Column(Enum('premium', 'apv', 'pensionista', 'normal'),
                      nullable=False)
    period = Column(Unicode(6), nullable=False)
    ip_addr = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.now)


if __name__ == '__main__':
    from sqlalchemy import create_engine

    import settings

    engine = create_engine(settings.DATABASE_DSN, echo=settings.DEBUG)
    Entity.metadata.create_all(engine)
