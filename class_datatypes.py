from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, Float, DateTime
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base, relationship, backref
from sqlalchemy.ext.hybrid import hybrid_property

Base = declarative_base()

class GDACS(Base):
    __tablename__ = 'gdacs'
    id = Column(Integer, primary_key=True)
    content = Column(Text)
    date_time = Column(DateTime)
    source_type = Column(String(50), default='GDACS')
    location = Column(Text)
    processed = Column(Boolean, default=False)

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
    disaster_type = Column(String)
    probability = Column(Float)    # 灾害的概率
    source_type = Column(String(50))  # 来源类型：'topic' 或 'reply'
    source_id = Column(Integer)       # 原始话题或回复的ID
    authenticity_rating = Column(Float, default=0.0)
    accuracy_rating = Column(Float, default=0.0)
    authenticity_raters = Column(Integer, default=0)
    accuracy_raters = Column(Integer, default=0)
    delete_votes = Column(Integer, default=0)  # Track votes for deletion
    votes = relationship('Vote', back_populates='result')
    processed = Column(Boolean, default=False)
    warning_id = Column(Integer, ForeignKey('warnings.id'))

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

class Warning(Base):
    __tablename__ = 'warnings'
    id = Column(Integer, primary_key=True)
    disaster_type = Column(String)
    disaster_time = Column(String)  # 考虑时间字段的实际需求
    disaster_location = Column(String)
    results = relationship('Result', back_populates='warning')

Result.warning = relationship('Warning', back_populates='results')

class Subscriber(Base):
    __tablename__ = 'subscribers'
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False)
    password = Column(String, nullable=False)  # 新增密码字段
    votes = relationship('Vote', back_populates='subscriber')    
    
class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('results.id'), nullable=False)
    vote_type = Column(String(50))  # Can be 'delete', 'upvote', etc., depending on your needs

    subscriber = relationship('Subscriber', back_populates='votes')
    result = relationship('Result', back_populates='votes')
    
class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('results.id'), nullable=False)
    type = Column(String(50))  # 'authenticity' or 'accuracy'
    rating = Column(Float)

    # Relationships with backrefs
    user = relationship('Subscriber', backref=backref('ratings', cascade='all, delete-orphan'))
    message = relationship('Result', backref=backref('ratings', cascade='all, delete-orphan'))
