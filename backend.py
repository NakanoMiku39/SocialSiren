import threading
from multiprocessing import Process
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
from sqlalchemy.orm import scoped_session, sessionmaker
import configparser
from selenium.webdriver.chrome.options import Options
import class_datatypes
import class_model
import class_spider
import class_GDACSspider
import class_translator
import class_SubscriptionSystem
import class_DataManager
import class_CaptchaService
import class_ChatGPT
from class_datatypes import Warning, Result, UsersComments, WarningRating, WarningVote, Vote, Rating
from datetime import datetime
from sqlalchemy import create_engine, desc, asc
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import os
import time

class Backend:
    def __init__(self, db_path):
        print("[Debug] Creating Backend")
        self.session = self.init_db(db_path)
        self.create_tables()
        self.translator, self.model, self.subscriptionsystem, self.datamanager, self.captchaservice = self.init_subsystems()
        self.spider_event = threading.Event()
        self.gdacs_event = threading.Event()
        self.options = Options()
        # options.add_argument("--headless")  # 设置为无头模式
        self.options.add_argument('--disable-gpu')
        self.options.add_argument("--no-sandbox") 
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument(r"user-data-dir=/home/nakanomiku/.config/google-chrome")
        self.options.add_experimental_option("prefs", {
            "download.default_directory": '/home/nakanomiku/Downloads/',
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })


        # self.schedule_tasks()
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

        
        # 初始化 DisasterTweetModel
        # train_path = 'dataset/train.csv'
        # test_path = 'dataset/test.csv'
        # model = class_model.DisasterTweetModel(train_path, test_path, self.session)
        model = class_ChatGPT.LangChainModel(self.session, config['GPT']['apikey'])

        # 初始化SubscriptionSystem
        subscriptionsystem = class_SubscriptionSystem.SubscriptionSystem('220.197.30.134', 25,  config['User']['email'], config['User']['password'],  self.session)

        # 初始化DataManager
        datamanager = class_DataManager.DataManager(self.session)
        
        # 初始化CaptchaService
        captchaservice = class_CaptchaService.CaptchaService()
        
        return translator, model, subscriptionsystem, datamanager, captchaservice

    def spider_task(self):
        while True:
            self.spider_event.wait()
            # 初始化 Spider
            config = configparser.ConfigParser()
            config.read('config.ini')
            spider = class_spider.Spider(config, self.session, self.options)
            print("Spider is running...")
            spider.run()  # 假设 Spider 有一个 run 方法
            # time.sleep(60)  # 运行一定时间后停止
            print("Spider is stopping...")
            spider.stop()  # 假设 Spider 有一个 stop 方法
            self.spider_event.clear()
            self.gdacs_event.set()

    def gdacs_task(self):
        while True:
            self.gdacs_event.wait()
            print("GDACS is running...")
            gdacsspider = class_GDACSspider.GDACSSpider("/home/nakanomiku/Downloads/", "./data", self.session, self.options)
            gdacsspider.run()  # 假设 GDACS 有一个 run 方法
            # time.sleep(60)  # 运行一定时间后停止
            print("GDACS is stopping...")
            gdacsspider.stop()  # 假设 GDACS 有一个 stop 方法
            self.gdacs_event.clear()
            self.spider_event.set()
            
    def run_subsystems(self):
        """启动子系统线程"""
        print("[Debug] Waking up subsystems")
        translator_thread = threading.Thread(target=self.translator.run, daemon=True)
        # spider_thread = threading.Thread(target=self.spider.run, daemon=True)
        # gdacsspider_thread = threading.Thread(target=self.gdacs.run, daemon=True)
        model_thread = threading.Thread(target=self.model.run, daemon=True)
        subscriptionsystem_thread = threading.Thread(target=self.subscriptionsystem.run, daemon=True)
        # translator_thread.start()
        # spider_thread.start()
        # gdacsspider_thread.start()
        model_thread.start()
        subscriptionsystem_thread.start()
        threading.Thread(target=self.spider_task).start()
        threading.Thread(target=self.gdacs_task).start()
        self.spider_event.set()

    def get_all_results(self):
        """从数据库中获取所有结果记录"""
        try:
            results = self.session.query(Result).order_by(desc(Result.id)).all()
            return results
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
        
    def process_message(self, content):
        """处理并存储消息"""
        db_session = self.session()
        try:
            new_comment = UsersComments(
                content=content,
                date_time=datetime.now(),  # 使用当前时间
                processed=False
            )
            db_session.add(new_comment)
            db_session.commit()
            print(f"[Debug] Message stored: {content}")
            return {"status": "success", "message": "Message processed and stored successfully"}
        except Exception as e:
            db_session.rollback()
            print(f"[Debug] Error storing message: {e}")
            return {"status": "error", "message": "Failed to store the message"}
        finally:
            db_session.close()

    def get_user_votes_and_ratings(self, user_id):
        try:
            db_session = self.session()
            warning_votes = db_session.query(WarningVote).filter_by(user_id=user_id).all()
            result_votes = db_session.query(Vote).filter_by(user_id=user_id).all()
            warning_ratings = db_session.query(WarningRating).filter_by(user_id=user_id).all()
            result_ratings = db_session.query(Rating).filter_by(user_id=user_id).all()
            return {
                "warningVotes": [vote.to_dict() for vote in warning_votes],
                "resultVotes": [vote.to_dict() for vote in result_votes],
                "warningRatings": [rating.to_dict() for rating in warning_ratings],
                "resultRatings": [rating.to_dict() for rating in result_ratings]
            }
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
        
# 创建 Flask 应用
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://10.129.199.88:1111"])  # 确保CORS策略允许来自前端的请求
jwt = JWTManager(app)
app.secret_key = 'your_secret_key_here'  # 用于安全地保存 session 信息
app.config['SESSION_TYPE'] = 'filesystem'  # 使用文件系统存储会话
app.config['JWT_SECRET_KEY'] = 'your_secret_key_here'  # Change this!

os.environ['CUDA_VISIBLE_DEVICES'] = '-1'  # 正确禁用 GPU

backend = Backend('data/forum.db')  # 假设数据库文件名为 example.db

def calculate_average(total, count):
    return total / count if count > 0 else None

# 邮箱订阅服务
@app.route('/subscribe', methods=['POST'])
def subscribe():
    print("[Debug from Captcha] Captcha is now:", session)
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    user_captcha_response = data.get('captcha', '')
    original_captcha = session.get('captcha', '')

    print("User captcha:", user_captcha_response)
    print("Original captcha:", session.get('captcha', 'Not Set'))

    # 检查验证码
    if not user_captcha_response.lower() == original_captcha.lower():
        return jsonify({"status": "error", "message": "CAPTCHA validation failed"}), 403

    # 清除session中的验证码，确保每个验证码只使用一次
    session.pop('captcha', None)

    # 进行用户登录或注册逻辑
    user_exists, user_info = backend.subscriptionsystem.register_or_login(email, password)
    if user_exists:
        try:
            # 创建 JWT token
            access_token = create_access_token(identity=email)
            return jsonify({
                "message": "Login successful",
                "access_token": access_token
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    else:
        return jsonify({"error": "Invalid email or password"}), 400   
    
@app.route('/api/warnings', methods=['GET'])
def get_warnings():
    filters = {
        'disaster_type': None if request.args.get('disasterType') == 'all' else request.args.get('disasterType'),
    }
    order_by = request.args.get('orderBy', 'disaster_time')
    order_desc = request.args.get('orderDesc', 'true') in ['true', 'True', '1', True]
    
    print(f"[Debug] Filters: {filters}")
    print(f"[Debug] Order by: {order_by}, Order desc: {order_desc}")
    
    try:
        db_session = backend.session()
        query = db_session.query(Warning)

        if filters['disaster_type']:
            print(f"[Debug] Filtering by disaster_type: {filters['disaster_type']}")
            query = query.filter(Warning.disaster_type == filters['disaster_type'])

        if order_by and hasattr(Warning, order_by):
            print(f"[Debug] Ordering by: {order_by}")
            order_function = desc if order_desc else asc
            query = query.order_by(order_function(getattr(Warning, order_by)))
        else:
            print(f"[Debug] Invalid order_by attribute: {order_by}")

        warnings = query.all()
        result = []
        for warning in warnings:
            related_results = db_session.query(Result).filter(Result.warning_id == warning.id).all()
            result.append({
                'id': warning.id,
                'disaster_type': warning.disaster_type,
                'disaster_location': warning.disaster_location,
                'disaster_time': warning.disaster_time,
                'authenticity_average': calculate_average(warning.authenticity_rating, warning.authenticity_raters),
                'accuracy_average': calculate_average(warning.accuracy_rating, warning.accuracy_raters),
                'authenticity_count': warning.authenticity_raters,  # 确保返回评分人数
                'accuracy_count': warning.accuracy_raters,  # 确保返回评分人数
                'related_tweets': [{
                    'id': r.id,
                    'content': r.content,
                    'is_disaster': r.is_disaster,
                    'disaster_type': r.disaster_type,
                    'probability': r.probability,
                    'source_type': r.source_type,
                    'source_id': r.source_id,
                    'date_time': r.date_time.isoformat() if r.date_time else None,
                    'authenticity_average': calculate_average(r.authenticity_rating, r.authenticity_raters),
                    'accuracy_average': calculate_average(r.accuracy_rating, r.accuracy_raters),
                    'authenticity_count': r.authenticity_raters,  # 确保返回评分人数
                    'accuracy_count': r.accuracy_raters,  # 确保返回评分人数
                    'hasVotedAuthenticity': False,  # Default to False, update with actual logic if needed
                    'hasVotedAccuracy': False,      # Default to False, update with actual logic if needed
                    'hasVotedDelete': r.delete_votes > 0  # Assume backend sends this flag
                } for r in related_results]
            })
        print(f"[Debug] Warnings retrieved: {len(result)}")
        return jsonify(result)
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve warnings"}), 500

@app.route('/api/gdacsMessages')
def get_gdacs_messages():
    filters = {
        'source_type': request.args.get('sourceType', 'GDACS')  # Default to 'GDACS'
    }
    order_by = request.args.get('orderBy', 'date_time')
    order_desc = request.args.get('orderDesc', 'true') in ['true', 'True', '1', True]

    results = backend.datamanager.get_data_gdacs(order_by=order_by, order_desc=order_desc)

    return jsonify([
        {
            'id': result.id,
            'content': result.content,
            'date_time': result.date_time.isoformat() if result.date_time else None,
            'source_type': result.source_type,
            'location': result.location
        } for result in results
    ])
    
# 从前端接收数据
@app.route('/api/send-message', methods=['POST'])
def send_message():
    print("[Debug from Captcha] Captcha is now:", session)
    data = request.get_json()
    user_captcha_response = data.get('captcha', '')
    original_captcha = session.get('captcha', '')

    print("User captcha:", user_captcha_response)
    print("Original captcha:", session.get('captcha', 'Not Set'))
    
    if not user_captcha_response.lower() == original_captcha.lower():
        return jsonify({"status": "error", "message": "CAPTCHA validation failed"}), 403

    message_content = data.get('content')
    backend.process_message(message_content)
    # 处理消息发送逻辑...
    return jsonify({"status": "success", "message": "Message sent successfully"})

# 向前端发送验证码
@app.route('/captcha')
def captcha():
    """返回一个验证码图像"""
    captcha_image = backend.captchaservice.get_captcha()
    print("[Debug from Captcha] Captcha is now:", session)
    # 确保 captcha_image 是一个正确的 BytesIO 流
    return send_file(captcha_image, mimetype='image/png')

@app.route('/api/rate-warning', methods=['POST'])
@jwt_required()
def rate_warning():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

    data = request.get_json()
    warning_id = data.get('warning_id')
    rating = data.get('rating')
    rating_type = data.get('type')

    db_session = backend.session()
    warning = db_session.query(Warning).get(warning_id)
    if not warning:
        return jsonify({'status': 'error', 'message': 'Warning not found'}), 404

    existing_rating = db_session.query(WarningRating).filter_by(user_id=user_id, warning_id=warning_id, type=rating_type).first()
    if existing_rating:
        return jsonify({'status': 'error', 'message': 'You have already rated this warning'}), 400

    new_rating = WarningRating(user_id=user_id, warning_id=warning_id, type=rating_type, rating=rating)
    db_session.add(new_rating)

    if rating_type == 'authenticity':
        warning.authenticity_rating += rating
        warning.authenticity_raters += 1
    elif rating_type == 'accuracy':
        warning.accuracy_rating += rating
        warning.accuracy_raters += 1
    else:
        return jsonify({'status': 'error', 'message': 'Invalid rating type'}), 400

    db_session.commit()

    return jsonify({
        'status': 'success',
        'authenticity_average': calculate_average(warning.authenticity_rating, warning.authenticity_raters),
        'accuracy_average': calculate_average(warning.accuracy_rating, warning.accuracy_raters),
        'authenticity_count': warning.authenticity_raters,
        'accuracy_count': warning.accuracy_raters
    })

@app.route('/api/delete-warning', methods=['POST'])
@jwt_required()
def delete_warning():
    user_id = get_jwt_identity()
    data = request.get_json()
    warning_id = data.get('warning_id')

    db_session = backend.session()
    warning = db_session.get(Warning, warning_id)

    if not warning:
        return jsonify({'status': 'error', 'message': 'Warning not found'}), 404

    existing_vote = db_session.query(WarningVote).filter_by(user_id=user_id, warning_id=warning_id, vote_type='delete').one_or_none()

    if existing_vote:
        return jsonify({'status': 'error', 'message': 'You have already voted to delete this warning'}), 409

    warning.delete_votes += 1

    new_vote = WarningVote(user_id=user_id, warning_id=warning_id, vote_type='delete')
    db_session.add(new_vote)

    if warning.delete_votes >= 1:  # Adjust the threshold as needed
        with db_session.no_autoflush:
            print("[Debug] Checking if the warning is related to any GDACS information...")
            # Check if the warning is related to any GDACS information
            if backend.model.is_related_to_any_gdacs(db_session, warning.disaster_type + warning.disaster_location):
                print("[Debug] Warning is related to GDACS information, deletion aborted.")
                db_session.commit()
                return jsonify({'status': 'error', 'message': 'Warning is related to GDACS information and cannot be deleted.'}), 403

            print("[Debug] Warning is not related to any GDACS information, proceeding with deletion...")
            for rating in warning.ratings:
                db_session.delete(rating)
            db_session.delete(warning)
            db_session.commit()
            return jsonify({'status': 'success', 'message': 'Warning deleted successfully'}), 200

    db_session.commit()
    print("[Debug] Delete vote recorded. Pending more votes.")
    return jsonify({'status': 'pending', 'message': 'Vote recorded. Pending more votes. Checking if the message is correct...'}), 202

@app.route('/api/rate-message', methods=['POST'])
@jwt_required()
def rate_message():
    user_id = get_jwt_identity()
    data = request.get_json()
    message_id = data.get('message_id')
    rating = data.get('rating')
    rating_type = data.get('type')

    db_session = backend.session()
    message = db_session.query(Result).get(message_id)
    if not message:
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    existing_rating = db_session.query(Rating).filter_by(user_id=user_id, message_id=message_id, type=rating_type).first()
    if existing_rating:
        return jsonify({'status': 'error', 'message': 'You have already rated this message'}), 400

    new_rating = Rating(user_id=user_id, message_id=message_id, type=rating_type, rating=rating)
    db_session.add(new_rating)

    if rating_type == 'authenticity':
        message.authenticity_rating += rating
        message.authenticity_raters += 1
    elif rating_type == 'accuracy':
        message.accuracy_rating += rating
        message.accuracy_raters += 1
    else:
        return jsonify({'status': 'error', 'message': 'Invalid rating type'}), 400

    db_session.commit()

    return jsonify({
        'status': 'success',
        'authenticity_average': calculate_average(message.authenticity_rating, message.authenticity_raters),
        'accuracy_average': calculate_average(message.accuracy_rating, message.accuracy_raters),
        'authenticity_count': message.authenticity_raters,
        'accuracy_count': message.accuracy_raters
    })

@app.route('/api/delete-message', methods=['POST'])
@jwt_required()
def delete_message():
    user_id = get_jwt_identity()
    data = request.get_json()
    message_id = data.get('message_id')

    db_session = backend.session()
    message = db_session.get(Result, message_id)
    if not message:
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    existing_vote = db_session.query(Vote).filter_by(user_id=user_id, message_id=message_id, vote_type='delete').one_or_none()

    if existing_vote:
        return jsonify({'status': 'error', 'message': 'You have already voted to delete this message'}), 409

    message.delete_votes += 1

    new_vote = Vote(user_id=user_id, message_id=message_id, vote_type='delete')
    db_session.add(new_vote)

    if message.delete_votes >= 1:  # Adjust the threshold as needed
        with db_session.no_autoflush:
            print("[Debug] Checking if the message is related to any GDACS information...")
            # Check if the message is related to any GDACS information
            if backend.model.is_related_to_any_gdacs(db_session, message.content):
                print("[Debug] Message is related to GDACS information, deletion aborted.")
                db_session.commit()
                return jsonify({'status': 'error', 'message': 'Message is related to GDACS information and cannot be deleted.'}), 403

            print("[Debug] Message is not related to any GDACS information, proceeding with deletion...")
            for rating in message.ratings:
                db_session.delete(rating)
            db_session.delete(message)
            db_session.commit()
            return jsonify({'status': 'success', 'message': 'Message deleted successfully'}), 200

    db_session.commit()
    print("[Debug] Delete vote recorded. Pending more votes.")
    return jsonify({'status': 'pending', 'message': 'Vote recorded. Pending more votes. Checking if the message is correct...'}), 202

@app.route('/api/user-votes-and-ratings', methods=['GET'])
@jwt_required()
def get_user_votes_and_ratings():
    user_id = get_jwt_identity()
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

    db_session = backend.session()
    try:
        result_votes = db_session.query(Vote).filter_by(user_id=user_id).all()
        warning_votes = db_session.query(WarningVote).filter_by(user_id=user_id).all()
        result_ratings = db_session.query(Rating).filter_by(user_id=user_id).all()
        warning_ratings = db_session.query(WarningRating).filter_by(user_id=user_id).all()

        response_data = {
            'resultVotes': [{'message_id': vote.message_id, 'vote_type': vote.vote_type} for vote in result_votes],
            'warningVotes': [{'warning_id': vote.warning_id, 'vote_type': vote.vote_type} for vote in warning_votes],
            'resultRatings': [{'message_id': rating.message_id, 'type': rating.type} for rating in result_ratings],
            'warningRatings': [{'warning_id': rating.warning_id, 'type': rating.type} for rating in warning_ratings],
        }

        return jsonify(response_data), 200
    except Exception as e:
        print(f"An error occurred: {e}")
        return jsonify({"status": "error", "message": "Failed to retrieve user votes and ratings"}), 500
    finally:
        db_session.close()

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False, debug=True, port=2222)
