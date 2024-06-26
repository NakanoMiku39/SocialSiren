from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re
from class_datatypes import Topics, Replies
from datetime import datetime
from lock import db_lock

class Spider:
    def __init__(self, config, Session, options) -> None:
        self.username = config['User']['username']  # 学号
        self.password = config['User']['password']  # 密码
        self.entries = config['User']['entries']  # 希望爬取的树洞数
        self.mode = config['User']['mode']  # 爬虫运行模式
        self.timeout = config['User']['timeout']  # 树洞刷新间隔
        self.google = None
        self.Session = Session
        self.initialize_driver(options)
        print("[Debug] Spider initialized")

    def initialize_driver(self, options):
        try:
            self.google = webdriver.Chrome(options=options)
        except Exception as e:
            print(f"[Error] Failed to initialize WebDriver: {e}")
            self.clean_up()
            raise e

    def login(self):
        try:
            self.google.get("https://treehole.pku.edu.cn/web/")
            time.sleep(5)
            if "login" in self.google.current_url:
                print("Login required")
                username_input = self.google.find_element(By.XPATH, "//input[@type='text']")
                password_input = self.google.find_element(By.XPATH, "//input[@type='password']")
                if not username_input.get_attribute("value"):
                    username_input.send_keys(self.username)
                if not password_input.get_attribute("value"):
                    password_input.send_keys(self.password)
                self.google.find_element(By.XPATH, "//input[@type='checkbox']").click()
                self.google.find_element(By.XPATH, "//button[contains(text(),'登录')]").click()
                time.sleep(5)
                if "login" in self.google.current_url:
                    time.sleep(30)
            print("[Debug] Logged in")
        except Exception as e:
            print(f"[Error] Login failed: {e}")
            self.clean_up()
            raise e

    def realtime(self):
        try:
            time.sleep(int(self.timeout))
            refresh = self.google.find_element(By.CSS_SELECTOR, "span.icon.icon-refresh")
            refresh.click()
            self.google.find_element(By.XPATH, "//div[contains(@class,'title-bar')]").click()
            time.sleep(random.randint(3, 5))
            flow_items = self.google.find_elements(By.XPATH, "//div[contains(@class,'flow-item-row flow-item-row-with-prompt')]")
            self.crawlFlowItems(flow_items)
            print("New entries add: %d" % len(flow_items))
        except Exception as e:
            print(f"[Error] Realtime processing failed: {e}")
            self.clean_up()
            raise e

    def crawlFlowItems(self, flow_items):
        db_session = self.Session()
        print("[Debug] Spider tries to write to database")
        try:
            for flow_item in flow_items:
                flow_item.click()
                time.sleep(random.randint(1, 5))
                sidebar = WebDriverWait(self.google, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'sidebar')]"))
                )
                headers = sidebar.find_elements(By.XPATH, "//div[contains(@class,'box-header box-header-top-icon')]")
                codes_in_sidebar = sidebar.find_elements(By.CLASS_NAME, "box-id")
                box_contents_in_sidebar = sidebar.find_elements(By.XPATH, "//div[contains(@class,'box-content box-content-detail')]")

                for index, (header, code, box_content) in enumerate(zip(headers, codes_in_sidebar, box_contents_in_sidebar)):
                    code = int(code.text[1:])
                    full_header_text = header.text
                    date_time_match = re.search(r'(\d{4}-)?\d{2}-\d{2} \d{2}:\d{2}', full_header_text)
                    date_time = date_time_match.group() if date_time_match else "Unknown Date-Time"

                    try:
                        if date_time.startswith('20'):
                            date_time_obj = datetime.strptime(date_time, "%Y-%m-%d %H:%M")
                        else:
                            current_year = datetime.now().year
                            date_time_obj = datetime.strptime(f"{current_year}-{date_time}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        print("Error: Incorrect date format.")
                        date_time_obj = None

                    with db_session.no_autoflush:
                        if index == 0:
                            existing_topic = db_session.query(Topics).filter_by(id=code).first()
                            if not existing_topic:
                                new_topic = Topics(id=code, content=box_content.text, date_time=date_time_obj)
                                with db_lock:
                                    db_session.add(new_topic)
                        else:
                            existing_reply = db_session.query(Replies).filter_by(id=code).first()
                            if not existing_reply:
                                new_reply = Replies(id=code, content=box_content.text, topic_id=int(codes_in_sidebar[0].text[1:]), date_time=date_time_obj)
                                with db_lock:
                                    db_session.add(new_reply)

                sidebar.find_element(By.CSS_SELECTOR, "span.icon.icon-close").click()
                time.sleep(random.randint(1, 5))

                with db_lock:
                    db_session.commit()
                print("[Debug] Spider write successful")
        except Exception as e:
            print(f"[Error] Spider write failed: {e}")
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def run(self):
        print("[Debug] Spider activated")
        try:
            self.login()
            time.sleep(10)
            self.realtime()
        except Exception as e:
            print(f"[Error] Spider run failed: {e}")
            self.clean_up()
            raise e

    def stop(self):
        self.clean_up()

    def __del__(self):
        self.clean_up()

    def clean_up(self):
        if self.google:
            self.google.quit()
        self.Session.remove()
        print("Resources cleaned up successfully")
