from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, Float, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class Topics(Base):
    __tablename__ = 'topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    processed = Column(Boolean, default=False)

class Replies(Base):
    __tablename__ = 'replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    topic_id = Column(Integer, ForeignKey('topics.id'))
    date_time = Column(DateTime)
    processed = Column(Boolean, default=False)

class UsersComments(Base):
    __tablename__ = 'comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    processed = Column(Boolean, default=False)

class TranslatedTopics(Base):
    __tablename__ = 'translated_topics'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    processed = Column(Boolean, default=False)

class TranslatedReplies(Base):
    __tablename__ = 'translated_replies'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    topic_id = Column(Integer, ForeignKey('translated_topics.id'))
    processed = Column(Boolean, default=False)
    
class TranslatedUsersComments(Base):
    __tablename__ = 'translated_comments'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    processed = Column(Boolean, default=False)

class Result(Base):
    __tablename__ = 'results'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    is_disaster = Column(Boolean)  # 是否为灾害
    probability = Column(Float)    # 灾害的概率
    source_type = Column(String(50))  # 来源类型：'topic' 或 'reply'
    source_id = Column(Integer)       # 原始话题或回复的ID
    authenticity_rating = Column(Float, default=0.0)
    accuracy_rating = Column(Float, default=0.0)
    authenticity_raters = Column(Integer, default=0)
    accuracy_raters = Column(Integer, default=0)    
    processed = Column(Boolean, default=False)
        
    @hybrid_property
    def authenticity_average(self):
        if self.authenticity_raters > 0:
            return self.authenticity_rating / self.authenticity_raters
        return 0

    @hybrid_property
    def accuracy_average(self):
        if self.accuracy_raters > 0:
            return self.accuracy_rating / self.accuracy_raters
        return 0
    
class Subscriber(Base):
    __tablename__ = 'subscribers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)