from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, Float
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

Base = declarative_base()

class Topics(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(Text)
    processed = Column(Boolean, default=False)

class Replies(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    date_time = Column(Text)
    processed = Column(Boolean, default=False)

class TranslatedTopics(Base):
    __tablename__ = 'translated_topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(Text)
    processed = Column(Boolean, default=False)

class TranslatedReplies(Base):
    __tablename__ = 'translated_replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(Text)
    topic_id = Column(Integer, ForeignKey('translated_topics.id'))
    processed = Column(Boolean, default=False)
    
class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(Text)
    is_disaster = Column(Boolean)  # 是否为灾害
    probability = Column(Float)    # 灾害的概率
    source_type = Column(String(50))  # 来源类型：'topic' 或 'reply'
    source_id = Column(Integer)       # 原始话题或回复的ID
    processed = Column(Boolean, default=False)
        
class Subscriber(Base):
    __tablename__ = 'subscribers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)