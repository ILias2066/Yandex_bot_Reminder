from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()
engine = create_engine("sqlite:///calendar_bot.db", echo=True)
Session = sessionmaker(bind=engine)
session = Session()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True, nullable=False)
    timezone = Column(String, default="UTC")
    calendar_url = Column(String, nullable=True)  # Добавлено поле для хранения URL календаря
    events = relationship("Event", back_populates="user")

class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    event_name = Column(String, nullable=False)
    event_date = Column(DateTime, nullable=False)
    notification_time = Column(DateTime, nullable=False)
    user = relationship("User", back_populates="events")

Base.metadata.create_all(engine)  # Создание таблиц в базе данных
