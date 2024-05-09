import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.exc import IntegrityError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from class_datatypes import Subscriber, Result
import time
from werkzeug.security import generate_password_hash, check_password_hash

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
        db_session = self.Session()
        try:
            with db_session.no_autoflush:
                subscriber = Subscriber(email=email)
                db_session.add(subscriber)
                db_session.commit()
                self.state = 'Idle'
                print("[Debug] SubscriptionSystem write successful")
                return 'Subscriber added successfully'
        except IntegrityError:
            db_session.rollback()
            self.state = 'Idle'
            print("[Debug] SubscriptionSystem write failed")
            return 'Failed to add subscriber: Email already exists'
        finally:
            db_session.close()

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

    def get_all_subscribers(self):
        session = self.Session()
        try:
            subscribers = session.query(Subscriber.email).all()
            return [email[0] for email in subscribers]
        finally:
            session.close()
            
    def check_for_disasters_and_notify(self):
        session = self.Session()
        try:
            # 检查是否有标记为灾害的结果
            disaster_results = session.query(Result).filter_by(is_disaster=True).all()
            if disaster_results:
                # 如果有灾害结果，获取所有订阅者的邮件地址
                subscribers = self.get_all_subscribers()
                # 创建邮件内容
                message = "Alert! A disaster has been detected. Please check the system for more details."
                # 发送邮件给所有订阅者
                self.send_emails(subscribers, message)
        finally:
            session.close()
            
    def send_email(self, server, email, text):
        """Attempt to send an email and handle exceptions locally."""
        try:
            server.sendmail(self.email_username, email, text)
            print(f"[Debug] Email sent to {email}")
        except Exception as e:
            print(f"[Debug] Failed to send email to {email}: {e}")

    def send_emails(self, emails, message):
        db_session = self.Session()
        unprocessed_results = db_session.query(Result).filter_by(is_disaster=True, processed=False).all()
        if not unprocessed_results:
            print("[Debug] No unprocessed disaster results to send.")
            return
        
        server = smtplib.SMTP(self.email_host, self.email_port)
        server.starttls()  # Enable TLS
        server.login(self.email_username, self.email_password)
        
        try:
            with db_session.no_autoflush:
                for result in unprocessed_results:
                    msg = MIMEMultipart()
                    msg['From'] = self.email_username
                    msg['Subject'] = 'Urgent Notification'
                    body = f"Disaster Alert: {result.content} with probability {result.probability}"
                    msg.attach(MIMEText(body, 'plain'))
                    text = msg.as_string()

                    for email in emails:
                        msg['To'] = email
                        self.send_email(server, email, text)
                    
                    result.processed = True  # Mark as processed regardless of individual email success
                db_session.commit()
        except Exception as e:
            print(f"[Debug] Exception during email sending: {e}")
            db_session.rollback()
        finally:
            db_session.close()
            server.quit()
        
    def register_or_login(self, email, password):
        if self.state != 'Idle':
            return False, 'System is busy with another operation'
        self.state = 'RegisterOrLogin'
        db_session = self.Session()

        try:
            subscriber = db_session.query(Subscriber).filter_by(email=email).first()
            if subscriber:
                # 用户存在，验证密码
                if check_password_hash(subscriber.password, password):
                    self.state = 'Idle'
                    return True, 'Login successful'
                else:
                    self.state = 'Idle'
                    return False, 'Invalid password'
            else:
                # 新用户，注册
                hashed_password = generate_password_hash(password, method='sha256')
                new_subscriber = Subscriber(email=email, password=hashed_password)
                db_session.add(new_subscriber)
                db_session.commit()
                self.state = 'Idle'
                return True, 'Registration successful'
        except IntegrityError:
            db_session.rollback()
            self.state = 'Idle'
            return False, 'Email already exists'
        except Exception as e:
            db_session.rollback()
            print(f"Error in register_or_login: {str(e)}")  # 输出错误信息到日志
            raise  # 将异常再次抛出，确保外层可以捕获
        finally:
            db_session.close()
            
    def run(self):
        while True:
            self.check_for_disasters_and_notify()
            time.sleep(20)