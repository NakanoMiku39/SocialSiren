from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

Base = declarative_base()

class Topics(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)

class Replies(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    topic_id = Column(Integer, ForeignKey('topics.id'))

class TranslatedTopics(Base):
    __tablename__ = 'translated_topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    processed = Column(Boolean, default=False)

class TranslatedReplies(Base):
    __tablename__ = 'translated_replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    topic_id = Column(Integer, ForeignKey('translated_topics.id'))
    processed = Column(Boolean, default=False)
    
class Result(Base):
    __tablename__ = 'results'
    
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    result = Column(Text)
    source_type = Column(String(50))  # Either 'topic' or 'reply'
    source_id = Column(Integer)  # Store the ID of the source topic or reply
