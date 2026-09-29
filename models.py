from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime
from.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)

class History(Base):
    __tablename__ = "history"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    category = Column(String) # home, party, jewelry
    budget = Column(Integer)
    query = Column(Text)
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.now)