import threading
from flask import Flask, jsonify, request, send_file, session
from flask_cors import CORS
from sqlalchemy.orm import scoped_session, sessionmaker
import configparser
from selenium.webdriver.chrome.options import Options
import class_datatypes
import class_model
import class_spider
import class_translator
import class_SubscriptionSystem
import class_DataManager
import class_CaptchaService
from class_datatypes import Result, UsersComments, Vote, Rating
from datetime import datetime
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, scoped_session
from flask_jwt_extended import create_access_token, JWTManager, jwt_required, get_jwt_identity
import os

class Backend:
    def __init__(self, db_path):
        print("[Debug] Creating Backend")
        self.session = self.init_db(db_path)
        self.create_tables()
        self.translator, self.spider, self.model, self.subscriptionsystem, self.datamanager, self.captchaservice = self.init_subsystems()
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

        # 初始化DataManager
        datamanager = class_DataManager.DataManager(self.session)
        
        # 初始化CaptchaService
        captchaservice = class_CaptchaService.CaptchaService()
        
        return translator, spider, model, subscriptionsystem, datamanager, captchaservice
    
    def run_subsystems(self):
        """启动子系统线程"""
        print("[Debug] Waking up subsystems")
        translator_thread = threading.Thread(target=self.translator.run, daemon=True)
        spider_thread = threading.Thread(target=self.spider.run, daemon=True)
        model_thread = threading.Thread(target=self.model.run, daemon=True)
        subscriptionsystem_thread = threading.Thread(target=self.subscriptionsystem.run, daemon=True)
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


# 创建 Flask 应用
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://10.129.199.88:1111"])
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
    email = request.json.get('email')
    password = request.json.get('password')
    # 假设 backend.subscriptionsystem.register_or_login 已正确实现并返回 (成功状态, 消息/用户信息)
    try:
        user_exists, user_info = backend.subscriptionsystem.register_or_login(email, password)
        if user_exists:
            # 创建 JWT token
            try:
                access_token = create_access_token(identity=email)
                return jsonify({
                    "message": "Login successful",
                    "access_token": access_token  # 发送 JWT 让前端可以使用它来维持会话状态
                }), 200
            except Exception as e:
                print("Failed to create access token:", str(e))
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Invalid email or password"}), 400
    except Exception as e:
        # 在开发和调试阶段，直接返回异常信息可以帮助快速定位问题
        # 在生产环境中，应考虑安全性，避免返回敏感信息
        return jsonify({"error": f"Internal Server Error: {str(e)}"}), 500    
    
# 向前端发送数据
@app.route('/api/messages')
def get_messages():
    # 接收前端参数，'all' 表示不过滤该条件
    filters = {
        'source_type': None if request.args.get('sourceType') == 'all' else request.args.get('sourceType'),
        'is_disaster': None if request.args.get('isDisaster') == 'all' else request.args.get('isDisaster') in ['true', 'True', '1', True] if request.args.get('isDisaster') is not None else None
    }
    order_by = request.args.get('orderBy', 'date_time')
    order_desc = request.args.get('orderDesc', 'true') in ['true', 'True', '1', True]    
    print("[Debug from Captcha] Captcha is now:", session.get('captcha', ''))
    print("filters:", filters)
    print("order_by:", order_by)
    print("order_desc:", order_desc)
    results = backend.datamanager.get_data(filters=filters, order_by=order_by, order_desc=order_desc)
        
    return jsonify([
        {
            'id': result.id,
            'content': result.content,
            'is_disaster': result.is_disaster,
            'probability': result.probability,
            'source_type': result.source_type,
            'source_id': result.source_id,
            'date_time': result.date_time.isoformat() if result.date_time else None,
            'authenticity_average': calculate_average(result.authenticity_rating, result.authenticity_raters),
            'accuracy_average': calculate_average(result.accuracy_rating, result.accuracy_raters),
            'authenticity_count': result.authenticity_raters,
            'accuracy_count': result.accuracy_raters
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

@app.route('/api/rate-message', methods=['POST'])
@jwt_required()  # Ensure the user is authenticated
def rate_message():
    user_id = get_jwt_identity()  # Assuming JWT authentication is used
    if not user_id:
        return jsonify({'status': 'error', 'message': 'Authentication required'}), 401

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
        'message': 'Rating updated successfully.',
        'authenticity_average': calculate_average(message.authenticity_rating, message.authenticity_raters),
        'accuracy_average': calculate_average(message.accuracy_rating, message.accuracy_raters),
        'authenticity_count': message.authenticity_raters,
        'accuracy_count': message.accuracy_raters
    })
    
@app.route('/api/delete-message', methods=['POST'])
@jwt_required()  # Ensure the user is authenticated
def delete_message():
    user_id = get_jwt_identity()
    data = request.get_json()
    print("Received data:", data)
    message_id = data.get('message_id')

    db_session = backend.session()
    message = db_session.query(Result).get(message_id)
    print("message:", message, "message_id:", message_id)

    if not message:
        return jsonify({'status': 'error', 'message': 'Message not found'}), 404

    # Check if the user has already voted for this message
    existing_vote = db_session.query(Vote).filter_by(user_id=user_id, message_id=message_id, vote_type='delete').one_or_none()

    if existing_vote:
        return jsonify({'status': 'error', 'message': 'You have already voted to delete this message'}), 409

    # Increment the delete votes count
    message.delete_votes += 1

    # Record the new vote
    new_vote = Vote(user_id=user_id, message_id=message_id, vote_type='delete')
    db_session.add(new_vote)

    # Check if the vote threshold is met to delete the message
    if message.delete_votes >= 10:  # Example threshold
        db_session.delete(message)
        db_session.commit()
        return jsonify({'status': 'success', 'message': 'Message deleted successfully'}), 200

    db_session.commit()
    return jsonify({'status': 'pending', 'message': 'Vote recorded. Pending more votes.'}), 202

if __name__ == '__main__':
    app.run(host='0.0.0.0', use_reloader=False, debug=True, port=2222)  
