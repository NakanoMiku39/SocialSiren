import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.exc import IntegrityError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from class_datatypes import Subscriber

class SubscriptionSystem:
    def __init__(self, email_host, email_port, email_username, email_password, Session):
        self.state = 'Idle'
        self.email_host = email_host
        self.email_port = email_port
        self.email_username = email_username
        self.email_password = email_password
        self.Session = Session
        print("[Debug] SubscriptionSystem initialized")


    def add_subscriber(self, email):
        if self.state != 'Idle':
            return 'System is busy with another operation'
        self.state = 'AddingSubscriber'
        session = self.Session()
        try:
            subscriber = Subscriber(email=email)
            session.add(subscriber)
            session.commit()
            self.state = 'Idle'
            print("[Debug] SubscriptionSystem write successful")
            return 'Subscriber added successfully'
        except IntegrityError:
            session.rollback()
            self.state = 'Idle'
            print("[Debug] SubscriptionSystem write failed")
            return 'Failed to add subscriber: Email already exists'
        finally:
            session.close()

    def remove_subscriber(self, email):
        if self.state != 'Idle':
            return 'System is busy with another operation'
        self.state = 'RemovingSubscriber'
        session = self.Session()
        try:
            result = session.query(Subscriber).filter(Subscriber.email == email).delete()
            session.commit()
            if result == 0:
                self.state = 'Idle'
                return 'No such subscriber found'
            self.state = 'Idle'
            return 'Subscriber removed successfully'
        finally:
            session.close()

    def notify_subscribers(self, message):
        self.state = 'SendingNotifications'
        subscribers = self.get_all_subscribers()
        self.send_emails(subscribers, message)
        self.state = 'Idle'

    def get_all_subscribers(self):
        session = self.Session()
        try:
            subscribers = session.query(Subscriber.email).all()
            return [email[0] for email in subscribers]
        finally:
            session.close()