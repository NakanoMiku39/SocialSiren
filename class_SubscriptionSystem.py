import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from sqlalchemy.exc import IntegrityError
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from class_datatypes import Subscriber, Result
import time

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
            
    def send_emails(self, emails, message):
        # 登录到SMTP服务器
        db_session = self.Session()
        unprocessed_results = db_session.query(Result).filter_by(is_disaster=True, processed=False).all()
        if not unprocessed_results:
            print("[Debug] No unprocessed disaster results to send.")
            return
        
        server = smtplib.SMTP(self.email_host, self.email_port)
        server.starttls()  # 启动TLS
        server.login(self.email_username, self.email_password)
        
        # 创建邮件内容
        msg = MIMEMultipart()
        msg['From'] = self.email_username
        msg['Subject'] = 'Urgent Notification'
        
        # 发送邮件给每个订阅者
        try:
            with db_session.no_autoflush:
                for result in unprocessed_results:
                    body = f"Disaster Alert: {result.content} with probability {result.probability}"
                    msg.attach(MIMEText(body, 'plain'))
                    text = msg.as_string()
                    for email in emails:
                        msg['To'] = email
                        server.sendmail(self.email_username, email, text)
                        print(f"[Debug] Email sent to {email} regarding {result.id}")
                    # 标记结果为已处理
                    result.processed = True
                db_session.commit()
        except Exception as e:
            # 如果出现异常，进行回滚
            print("[Debug] Email Sent failed")
            db_session.rollback()
        finally:
            db_session.close()
            
        # 断开SMTP服务器连接
        server.quit()
            
    def run(self):
        while True:
            self.check_for_disasters_and_notify()
            time.sleep(20)