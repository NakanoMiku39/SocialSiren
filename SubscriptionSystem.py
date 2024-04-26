import sqlite3
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class SubscriptionSystem:
    def __init__(self, email_host, email_port, email_username, email_password):
        self.state = 'Idle'
        self.db_path = 'subscribers.db'
        self.email_host = email_host
        self.email_port = email_port
        self.email_username = email_username
        self.email_password = email_password
        self.initialize_db()

    def initialize_db(self):
        with self.db_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS subscribers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT NOT NULL UNIQUE
                );
            ''')

    def db_connection(self):
        return sqlite3.connect(self.db_path)

    def add_subscriber(self, email):
        if self.state != 'Idle':
            return 'System is busy with another operation'
        self.state = 'AddingSubscriber'
        try:
            with self.db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('INSERT INTO subscribers (email) VALUES (?)', (email,))
                conn.commit()
                self.state = 'Idle'
                return 'Subscriber added successfully'
        except sqlite3.IntegrityError:
            self.state = 'Idle'
            return 'Failed to add subscriber: Email already exists'

    def remove_subscriber(self, email):
        if self.state != 'Idle':
            return 'System is busy with another operation'
        self.state = 'RemovingSubscriber'
        with self.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM subscribers WHERE email = ?', (email,))
            if cursor.rowcount == 0:
                self.state = 'Idle'
                return 'No such subscriber found'
            conn.commit()
            self.state = 'Idle'
            return 'Subscriber removed successfully'

    def notify_subscribers(self, message):
        self.state = 'SendingNotifications'
        subscribers = self.get_all_subscribers()
        self.send_emails(subscribers, message)
        self.state = 'Idle'

    def get_all_subscribers(self):
        with self.db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT email FROM subscribers')
            return [row[0] for row in cursor.fetchall()]

    def send_emails(self, emails, message):
        from_address = self.email_username
        msg = MIMEMultipart()
        msg['From'] = from_address
        msg['Subject'] = 'Urgent Notification'
        body = message
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(self.email_host, self.email_port)
        server.starttls()
        server.login(from_address, self.email_password)
        for email in emails:
            msg['To'] = email
            text = msg.as_string()
            server.sendmail(from_address, email, text)
        server.quit()

# Example Usage
if __name__ == '__main__':
    system = SubscriptionSystem('smtphz.qiye.163.com', 587, '***', '***')
    system.add_subscriber('***')
    system.notify_subscribers('This is a test alert!')
