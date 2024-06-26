import time
from sqlalchemy.exc import SQLAlchemyError, OperationalError
from class_datatypes import Topics, Replies, UsersComments, Result, Warning, GDACS
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
from lock import db_lock

class LangChainModel:
    def __init__(self, Session, apikey, model_name='gpt-3.5-turbo'):  # gpt-3.5-turbo or gpt-4
        self.Session = Session
        self.model_name = model_name
        self.llm = ChatOpenAI(api_key=apikey, model_name=model_name)
        self.prompt = PromptTemplate.from_template(
            """
            你现在是一个灾害专家，现在我会给你一系列的文本输入，你需要判断该文本是否为灾害相关推文，如果是，从中提取出灾害的类型，如果可能，从中提取出灾害的时间和地点，如果不是则不需要给出之后三个信息，你的输出格式如下，填写这四个字段，除此之外不要再给出任何额外输出，无论我的输入是什么，你必须永远严格按照以上的要求并用英语回答：
            是否为灾害 灾害类型 时间 地点

            例子：十问猜一本小说～（只能是非问和选择问）
            回答：No
            例子：无锡今天地震了
            回答：Yes earthquake Wuxi 2024-5-23
            例子：也门洪水了
            回答：Yes flood Yemen
            例子：哪里爆炸了
            回答：Yes explosion
            例子：今天有台风
            回答：Yes typhoon

            Human: {question}
            AI:
            """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        print("[Debug] Model initialized")

    def __del__(self):
        self.Session.remove()  # Close session

    def parse_response(self, response):
        parts = response.split()
        if parts[0] == "No":
            return False, "", "", ""
        elif parts[0] == "Yes":
            disaster_type = parts[1] if len(parts) > 1 else ""
            location = parts[2] if len(parts) > 2 else ""
            time = parts[3] if len(parts) > 3 else ""
            return True, disaster_type, location, time
        return False, "", "", ""

    def create_warning_if_needed(self, db_session, is_disaster, disaster_type, disaster_location, disaster_time):
        if is_disaster:
            existing_warning = db_session.query(Warning).filter(
                Warning.disaster_type == disaster_type,
                Warning.disaster_location == disaster_location,
                Warning.disaster_time == disaster_time,
            ).first()
            if not existing_warning:
                with db_session.no_autoflush:
                    new_warning = Warning(
                        disaster_type=disaster_type,
                        disaster_location=disaster_location,
                        disaster_time=disaster_time,
                    )
                    with db_lock:
                        db_session.add(new_warning)
                        db_session.flush()  # Ensure the warning ID is available
                return new_warning.id
            return existing_warning.id
        return None

    def process_and_save_results(self, db_session, items, source_type, max_retries=5):
        for item in items:
            retries = 0
            while retries < max_retries:
                try:
                    original = db_session.query(source_type).filter(source_type.id == item.id).first()
                    if original:
                        question = item.content
                        response = self.chain.run({"question": question})
                        is_disaster, disaster_type, disaster_location, disaster_time = self.parse_response(response)
                        if is_disaster:
                            with db_session.no_autoflush:
                                warning_id = self.create_warning_if_needed(db_session, is_disaster, disaster_type, disaster_location, disaster_time)
                                new_result = Result(
                                    source_id=original.id,
                                    content=original.content,  # Use original content
                                    date_time=item.date_time,
                                    is_disaster=1,
                                    probability=1.0,  # Assume high confidence for simplicity
                                    disaster_type=disaster_type,
                                    source_type=source_type.__tablename__,
                                    warning_id=warning_id
                                )
                                with db_lock:
                                    db_session.add(new_result)
                        item.processed = True  # Ensure the processed flag is set for all items
                        db_session.commit()  # Commit after processing each item
                        print(f"Processed {source_type.__tablename__} {original.id}")
                        break  # 成功处理后跳出重试循环
                except OperationalError as e:
                    retries += 1
                    print(f"Database is locked, retrying ({retries}/{max_retries})...")
                    time.sleep(1)
                except Exception as e:
                    print(f"Failed processing {source_type.__tablename__} {original.id}: {str(e)}")
                    db_session.rollback()  # Rollback if any error occurs
                    raise

    def predict_and_save(self):
        while True:
            db_session = self.Session()
            try:
                print("[Debug] Checking for new data to process...")
                topics = db_session.query(Topics).filter(Topics.processed == False).all()
                replies = db_session.query(Replies).filter(Replies.processed == False).all()
                comments = db_session.query(UsersComments).filter(UsersComments.processed == False).all()

                with db_session.no_autoflush:
                    self.process_and_save_results(db_session, topics, Topics)
                    self.process_and_save_results(db_session, replies, Replies)
                    self.process_and_save_results(db_session, comments, UsersComments)

                print("[Debug] Model write successful, sleeping for 10 seconds...")
                time.sleep(10)
            except SQLAlchemyError as db_err:
                db_session.rollback()
                print(f"Database error during processing: {db_err}")
            except Exception as e:
                db_session.rollback()
                print(f"Error during processing: {e}")
            finally:
                db_session.close()
                print("[Debug] Database session closed.")
    
    def is_related_to_gdacs(self, message_content, gdacs_content):
        question = f"Is the following message related to this GDACS information?\nMessage: {message_content}\nGDACS: {gdacs_content}\nYou must answer 'Yes' or 'No' only, no other extra sentences or vocabularies:"
        response = self.chain.run({"question": question})
        first_word = response.strip().split()[0]
        print(f"[Debug] GDACS related check response: {first_word}")
        return first_word.lower() == "yes"

    def is_related_to_any_gdacs(self, db_session, message_content):
        print("[Debug] Checking if message is related to any GDACS information...")
        with db_session.no_autoflush:
            gdacs_messages = db_session.query(GDACS).all()
            for gdacs_message in gdacs_messages:
                if self.is_related_to_gdacs(message_content, gdacs_message.content):
                    print("[Debug] Message is related to GDACS information.")
                    return True
        print("[Debug] Message is not related to any GDACS information.")
        return False
    
    def run(self):
        print("[Debug] Model activated")
        self.predict_and_save()
