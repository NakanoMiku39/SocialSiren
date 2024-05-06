import threading
from flask import Flask, jsonify, request
from flask_cors import CORS
from sqlalchemy.orm import scoped_session, sessionmaker
import configparser
from selenium.webdriver.chrome.options import Options
import class_datatypes
import class_model
import class_spider
import class_translator
import class_SubscriptionSystem
from class_datatypes import Result
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, scoped_session
import os

class Backend:
    def __init__(self, db_path):
        print("[Debug] Creating Backend")
        self.session = self.init_db(db_path)
        self.create_tables()
        self.translator, self.spider, self.model, self.subsriptionsystem = self.init_subsystems()
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
        
        # 初始化SubscriptionSystem
        subscriptionsystem = class_SubscriptionSystem.SubscriptionSystem('220.197.30.134', 25, config['User']['email'], config['User']['password'], self.session)

        return translator, spider, model, subscriptionsystem
    
    def run_subsystems(self):
        """启动子系统线程"""
        print("[Debug] Waking up subsystems")
        translator_thread = threading.Thread(target=self.translator.run, daemon=True)
        spider_thread = threading.Thread(target=self.spider.run, daemon=True)
        model_thread = threading.Thread(target=self.model.run, daemon=True)
        subscriptionsystem_thread = threading.Thread(target=self.subsriptionsystem.run, daemon=True)
        translator_thread.start()
        spider_thread.start()
        model_thread.start()
        subscriptionsystem_thread.start()

    def get_all_results(self):
        """从数据库中获取所有结果记录"""
        try:
            results = self.session.query(Result).order_by(desc(Result.id)).all()
            return results
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

# 创建 Flask 应用
app = Flask(__name__)
CORS(app)

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # 正确禁用 GPU

backend = Backend('data/forum.db')  # 假设数据库文件名为 example.db


# 邮箱订阅服务
@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.json['email']
    try:
        backend.subsriptionsystem.add_subscriber(email)
        return jsonify({"message": "Subscription successful"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/messages')
def get_messages():
    results = backend.get_all_results()
    return jsonify([
        {
            'id': result.id,
            'content': result.content,
            'is_disaster': result.is_disaster,
            'date_time': result.date_time,
            'probability': result.probability,
            'source_type': result.source_type,
            'source_id': result.source_id
        } for result in results
    ])

if __name__ == '__main__':
    app.run(use_reloader=False, debug=True, port=2222)  
