from selenium import webdriver
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import random
import re
from class_datatypes import Topics, Replies
from datetime import datetime

class Spider:
    def __init__(self, config, url, Session, options) -> None:
        self.username = config['User']['username'] # 学号
        self.password = config['User']['password'] # 密码
        self.entries = config['User']['entries'] # 希望爬取的树洞数
        self.mode = config['User']['mode'] # 爬虫运行模式
        self.timeout = config['User']['timeout'] # 树洞刷新间隔
        self.google = webdriver.Chrome(options=options)
        self.url = url
        self.Session = Session
        print("[Debug] Spider initialized")
        
    def login(self):
        self.google.get(self.url)
        time.sleep(5)
        # 伪造人工登陆
        if "login" in self.google.current_url: 
            print("Login required")
        # 定位账号输入框
            username_input = self.google.find_element(By.XPATH, "//input[@type='text']")
            # 定位密码输入框
            password_input = self.google.find_element(By.XPATH, "//input[@type='password']")

            # 输入账号和密码
            if not username_input.get_attribute("value"):
                username_input.send_keys(self.username)
            if not password_input.get_attribute("value"):
                password_input.send_keys(self.password)
            # 定位到同意服务协议的复选框并点击以打勾
            # 注意，这里假设页面上只有这一个复选框
            self.google.find_element(By.XPATH, "//input[@type='checkbox']").click()

            # 定位登录按钮并点击
            # 这里假设登录按钮是页面上唯一的按钮元素，或者是文本明确标识为“登录”的唯一按钮
            self.google.find_element(By.XPATH, "//button[contains(text(),'登录')]").click()
            time.sleep(5)
            # 为输入验证码空出时间
            if "login" in self.google.current_url:
                time.sleep(30)
        print("[Debug] Logged in")

    def realtime(self):      
        try:  
            while True:
                time.sleep(int(self.timeout))
                refresh = self.google.find_element(By.CSS_SELECTOR, "span.icon.icon-refresh") 
                refresh.click()
                self.google.find_element(By.XPATH, "//div[contains(@class,'title-bar')]").click()
                time.sleep(random.randint(3,5))
                flow_items = self.google.find_elements(By.XPATH, "//div[contains(@class,'flow-item-row flow-item-row-with-prompt')]")
                self.crawlFlowItems(flow_items)
                print("New entries add: %d" % len(flow_items))
                
        except KeyboardInterrupt:
            self.__del__()
            return
                      
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
         
                # Database operations
                for index, (header, code, box_content) in enumerate(zip(headers, codes_in_sidebar, box_contents_in_sidebar)):
                    code = int(code.text[1:])
                    full_header_text = header.text
                    date_time_match = re.search(r'\d{2}-\d{2} \d{2}:\d{2}', full_header_text)
                    date_time = date_time_match.group() if date_time_match else "Unknown Date-Time"
                    
                    try:
                        # Assume `date_time_str` is extracted from your web scraping logic
                        current_year = datetime.now().year
                        date_time_obj = datetime.strptime(f"{current_year}-{date_time}", "%Y-%m-%d %H:%M")
                    except ValueError:
                        print("Error: Incorrect date format.")
                        date_time_obj = None

                    with db_session.no_autoflush:
                        if index == 0:
                            # Check if the topic already exists                        
                            existing_topic = db_session.query(Topics).filter_by(id=code).first()
                            if not existing_topic:
                                new_topic = Topics(id=code, content=box_content.text, date_time=date_time_obj)
                                db_session.add(new_topic)
                        else:
                            existing_reply = db_session.query(Replies).filter_by(id=code).first()
                            if not existing_reply:
                                new_reply = Replies(id=code, content=box_content.text, topic_id=int(codes_in_sidebar[0].text[1:]), date_time=date_time_obj)
                                db_session.add(new_reply)
                
                sidebar.find_element(By.CSS_SELECTOR, "span.icon.icon-close").click()
                time.sleep(random.randint(1, 5))
        
                # 尝试提交所有翻译到数据库
                db_session.commit()
                print("[Debug] Spider write successful")
        except Exception as e:
            # 如果出现异常，进行回滚
            print("[Debug] Spider write failed")
            db_session.rollback()
            raise e
        finally:
            db_session.close()        
        
    def run(self):
        print("[Debug] Spider activated")
        self.login()
        time.sleep(10)
        self.realtime()
        
    def __del__(self):
        """资源清理"""
        self.Session.remove()  # 关闭 session
        self.google.quit()
        print("Quitted")