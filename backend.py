import threading
from flask import Flask, jsonify
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import configparser
from selenium.webdriver.chrome.options import Options
import class_spider
import class_translator
import class_datatypes
from sqlalchemy import create_engine, Table, Column, Integer, Text, ForeignKey, MetaData
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base


class Backend:
    def __init__(self, db_path):
        self.session = self.init_db(db_path)
        self.create_tables()
        self.translator, self.spider = self.init_subsystems()
        self.run_subsystems()
        
    def init_db(self, db_path):
        """初始化数据库连接池和会话"""
        engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
        Session = scoped_session(sessionmaker(bind=engine))
        return Session
    
    def create_tables(self):
        """创建数据库表"""
        class_datatypes.Base.metadata.create_all(self.session().bind)
        
    def init_subsystems(self):
        """初始化 Translator 和 Spider 子系统"""
        print("Initializing subsystems")
        # 读取配置文件
        config = configparser.ConfigParser()
        config.read('config.ini')

        # 初始化 Translator
        translator = class_translator.Translator("nllb-200-distilled-600M", self.session)

        # 初始化 Spider
        options = Options()
        # options.add_argument("--headless")  # 设置为无头模式
        options.add_argument(r"user-data-dir=/home/nakanomiku/.config/google-chrome")
        url = "https://treehole.pku.edu.cn/web/"
        spider = class_spider.Spider(config, url, self.session, options)
        
        return translator, spider
    
    def run_subsystems(self):
        """启动子系统线程"""
        print("[Debug] Waking up subsystems")
        translator_thread = threading.Thread(target=self.translator.run, daemon=True)
        spider_thread = threading.Thread(target=self.spider.run, daemon=True)
        translator_thread.start()
        # spider_thread.start()
        self.spider.run()
        
    def get_message(self):
        """从数据库获取信息并返回"""
        print("[Debug] Message received")
        cursor = self.session.execute("SELECT message FROM messages LIMIT 1;")
        message = cursor.fetchone()
        return {'message': message[0]} if message else {'message': 'No data'}

# 创建 Flask 应用
app = Flask(__name__)
backend = Backend('data/forum.db')  # 假设数据库文件名为 example.db

@app.route('/')
def index():
    """处理根 URL 的请求"""
    # return jsonify(backend.get_message())

if __name__ == '__main__':
    app.run(debug=True, port=9999)  # 更改运行端口为 8080
