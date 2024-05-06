import threading
from flask import Flask, jsonify, request
from sqlalchemy.orm import scoped_session, sessionmaker
import configparser
from selenium.webdriver.chrome.options import Options
import class_datatypes
import class_model
import class_spider
import class_translator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import os

class Backend:
    def __init__(self, db_path):
        self.session = self.init_db(db_path)
        self.create_tables()
        self.translator, self.spider, self.model = self.init_subsystems()
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
        options.add_argument('--disable-gpu')
        options.add_argument("--no-sandbox") 
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument(r"user-data-dir=/home/nakanomiku/.config/google-chrome")
        url = "https://treehole.pku.edu.cn/web/"
        spider = class_spider.Spider(config, url, self.session, options)
        
        # 初始化 DisasterTweetModel
        train_path = 'dataset/train.csv'
        test_path = 'dataset/test.csv'
        model = class_model.DisasterTweetModel(train_path, test_path, self.session)
        
        return translator, spider, model
    
    def run_subsystems(self):
        """启动子系统线程"""
        print("[Debug] Waking up subsystems")
        translator_thread = threading.Thread(target=self.translator.run, daemon=True)
        spider_thread = threading.Thread(target=self.spider.run, daemon=True)
        model_thread = threading.Thread(target=self.model.run, daemon=True)
        translator_thread.start()
        spider_thread.start()
        model_thread.start()
        # self.model.run()
        # self.spider.run()
        
    def get_message(self):
        """从数据库获取信息并返回"""
        print("[Debug] Message received")
        cursor = self.session.execute("SELECT message FROM messages LIMIT 1;")
        message = cursor.fetchone()
        return {'message': message[0]} if message else {'message': 'No data'}

# 创建 Flask 应用
app = Flask(__name__)

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # 正确禁用 GPU
app.debug = False
app.jinja_env.auto_reload = False
app.config['TEMPLATES_AUTO_RELOAD'] = False # 禁用watchdog
app.config['USE_RELOADER'] = False

backend = Backend('data/forum.db')  # 假设数据库文件名为 example.db

@app.route('/api/data', methods=['POST'])
def get_data():
    # 接收传入的 JSON 数据
    data = request.get_json()
    # 处理数据（这里仅作为示例返回相同的数据）
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=9999)  # 更改运行端口为 8080
