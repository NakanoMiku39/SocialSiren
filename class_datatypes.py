from sqlalchemy import create_engine, Table, Column, Integer, Text, ForeignKey, MetaData
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

class TranslatedReplies(Base):
    __tablename__ = 'translated_replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    topic_id = Column(Integer, ForeignKey('translated_topics.id'))
