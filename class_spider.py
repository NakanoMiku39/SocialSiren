from selenium import webdriver
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from sqlalchemy import create_engine, Table, Column, Integer, Text, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session
from webdriver_manager.chrome import ChromeDriverManager
import re
import sqlite3
import configparser
import time
import random

class spider:
    def __init__(self, config, url, db_path, options) -> None:
        self.username = config['User']['username'] # 学号
        self.password = config['User']['password'] # 密码
        self.entries = config['User']['entries'] # 希望爬取的树洞数
        self.mode = config['User']['mode'] # 爬虫运行模式
        self.timeout = config['User']['timeout'] # 树洞刷新间隔
        self.google = webdriver.Chrome(options=options)
        self.url = url
        self.db_session = self.init_db(db_path)
        self.create_tables()

    def init_db(self, db_path):
        """初始化数据库连接池和会话"""
        engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False}, echo=True)
        Session = scoped_session(sessionmaker(bind=engine))
        return Session()
    
    def create_tables(self):
        """创建数据库表"""
        metadata = MetaData()
        topics = Table('topics', metadata,
            Column('id', Integer, primary_key=True),
            Column('content', Text)
        )
        replies = Table('replies', metadata,
            Column('id', Integer, primary_key=True),
            Column('content', Text),
            Column('topic_id', Integer, ForeignKey('topics.id'))
        )
        metadata.create_all(self.db_session.bind)
        
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
        print("Logged in")

    def crawl(self):
        try:
            flow_items = self.google.find_elements(By.XPATH, "//div[contains(@class,'flow-item-row flow-item-row-with-prompt')]")
            action = ActionChains(self.google)
            # 点击是为了确保之后的ARROW_DOWN能正常下滑窗口
            self.google.find_element(By.XPATH, "//div[contains(@class,'title-bar')]").click()
            # 判断是否能爬取到指定数量的树洞，如果不能就继续往下滑动
            while len(flow_items) < int(self.entries):
                self.google.execute_script("window.scrollBy(0, 1000);")
                action.send_keys(Keys.ARROW_DOWN).perform()  # 模拟按下 Arrow Down 键
                flow_items = self.google.find_elements(By.XPATH, "//div[contains(@class,'flow-item-row flow-item-row-with-prompt')]")

            # 爬取
            self.crawlFlowItems(flow_items)
            print("Total entries: %d" % len(flow_items))
            
        except KeyboardInterrupt:
            self.__del__()
            return
        
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
        for flow_item in flow_items:
            # 打开每一条树洞的sidebar
            flow_item.click()
            # 等待sidebar加载出来
            time.sleep(random.randint(1, 5))
            sidebar = WebDriverWait(self.google, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'sidebar')]"))
            )
            
            # 获取指定数量树洞
            box_headers_in_sidebar = sidebar.find_elements(By.XPATH, "//div[contains(@class,'box-header box-header-top-icon')]")
            codes_in_sidebar = sidebar.find_elements(By.CLASS_NAME, "box-id")
            box_contents_in_sidebar = sidebar.find_elements(By.XPATH, "//div[contains(@class,'box-content box-content-detail')]")
            # 查询是否已经插入过了
            query = "SELECT * FROM topics WHERE id = ?"
            cursor = self.db.execute(query, (int(codes_in_sidebar[0].text[1:]),))
            if cursor.fetchone():
                print("Found repeated, quitting current crawl loop")
                close = sidebar.find_element(By.CSS_SELECTOR, "span.icon.icon-close") 
                close.click()
                break
                
            # 迭代洞中的每一条内容
            for index, (code, box_content) in enumerate(zip(codes_in_sidebar, box_contents_in_sidebar)):
                # 当前洞/回复号
                code = int(code.text[1:])
                
                if index == 0:
                    self.db.execute("INSERT INTO topics (id, content) VALUES (?, ?)", (code, box_content.text))
                else:
                    self.db.execute("INSERT INTO replies (id, content, topic_id) VALUES (?, ?, ?)", (code, box_content.text, int(codes_in_sidebar[0].text[1:])))
                
                # print(f"Header Text: {code}")
                # print(f"Content Text: {box_content.text}")    
                    
            # 关闭sidebar
            close = sidebar.find_element(By.CSS_SELECTOR, "span.icon.icon-close") 
            close.click()
            self.db_session.commit()  # 确保在适当时候提交会话
            time.sleep(random.randint(1, 5))
            
    def run(self):
        self.login()
        time.sleep(5)
        self.realtime()
        
    def __del__(self):
        """资源清理"""
        self.db_session.remove()  # 关闭 session
        self.google.quit()
        print("Quitted")