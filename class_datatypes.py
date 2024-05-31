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
    is_disaster = Column(Boolean)
    disaster_type = Column(String)
    probability = Column(Float)
    source_type = Column(String(50))
    source_id = Column(Integer)
    authenticity_rating = Column(Float, default=0.0)
    accuracy_rating = Column(Float, default=0.0)
    authenticity_raters = Column(Integer, default=0)
    accuracy_raters = Column(Integer, default=0)
    delete_votes = Column(Integer, default=0)
    processed = Column(Boolean, default=False)
    warning_id = Column(Integer, ForeignKey('warnings.id', ondelete='CASCADE'))

    warning = relationship('Warning', back_populates='results')
    votes = relationship('Vote', back_populates='result', cascade="all, delete-orphan")
    ratings = relationship('Rating', back_populates='result', cascade="all, delete-orphan")

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
    disaster_location = Column(String)
    disaster_time = Column(String)
    authenticity_rating = Column(Float, default=0.0)
    accuracy_rating = Column(Float, default=0.0)
    authenticity_raters = Column(Integer, default=0)
    accuracy_raters = Column(Integer, default=0)
    delete_votes = Column(Integer, default=0)
    processed = Column(Boolean, default=False)

    results = relationship('Result', back_populates='warning', cascade="all, delete-orphan")
    votes = relationship('WarningVote', back_populates='warning', cascade="all, delete-orphan")
    ratings = relationship('WarningRating', back_populates='warning', cascade="all, delete-orphan")

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
    password = Column(String, nullable=False)
    votes = relationship('Vote', back_populates='subscriber')
    warning_votes = relationship('WarningVote', back_populates='subscriber')
    ratings = relationship('Rating', back_populates='subscriber')
    warning_ratings = relationship('WarningRating', back_populates='subscriber')

class Vote(Base):
    __tablename__ = 'votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('results.id'), nullable=False)
    vote_type = Column(String(50))

    subscriber = relationship('Subscriber', back_populates='votes')
    result = relationship('Result', back_populates='votes')
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class WarningVote(Base):
    __tablename__ = 'warning_votes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    warning_id = Column(Integer, ForeignKey('warnings.id', ondelete='CASCADE'), nullable=False)
    vote_type = Column(String(50))

    subscriber = relationship('Subscriber', back_populates='warning_votes')
    warning = relationship('Warning', back_populates='votes')
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    message_id = Column(Integer, ForeignKey('results.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50))
    rating = Column(Float)

    subscriber = relationship('Subscriber', back_populates='ratings')
    result = relationship('Result', back_populates='ratings')
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class WarningRating(Base):
    __tablename__ = 'warning_ratings'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('subscribers.id'), nullable=False)
    warning_id = Column(Integer, ForeignKey('warnings.id', ondelete='CASCADE'), nullable=False)
    type = Column(String(50))
    rating = Column(Float)

    subscriber = relationship('Subscriber', back_populates='warning_ratings')
    warning = relationship('Warning', back_populates='ratings')
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
