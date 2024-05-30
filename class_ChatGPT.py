import time
from sqlalchemy.exc import SQLAlchemyError
from class_datatypes import Topics, Replies, UsersComments, Result, Warning
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

class LangChainModel:
    def __init__(self, Session, apikey, model_name='gpt-3.5-turbo'):
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
                new_warning = Warning(
                    disaster_type=disaster_type,
                    disaster_location=disaster_location,
                    disaster_time=disaster_time,
                )
                db_session.add(new_warning)
                db_session.flush()  # Ensure the warning ID is available
                return new_warning.id
            return existing_warning.id
        return None

    def process_and_save_results(self, db_session, items, source_type):
        for item in items:
            original = db_session.query(source_type).filter(source_type.id == item.id).first()
            if original:
                try:
                    question = item.content
                    response = self.chain.run({"question": question})
                    is_disaster, disaster_type, disaster_location, disaster_time= self.parse_response(response)
                    if is_disaster:
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
                        db_session.add(new_result)
                        item.processed = True
                        print(f"Processed {source_type.__tablename__} {original.id}")
                except Exception as e:
                    print(f"Failed processing {source_type.__tablename__} {original.id}: {str(e)}")

    def predict_and_save(self):
        db_session = self.Session()
        try:
            while True:
                print("[Debug] Checking for new data to process...")
                topics = db_session.query(Topics).filter(Topics.processed == False).all()
                replies = db_session.query(Replies).filter(Replies.processed == False).all()
                comments = db_session.query(UsersComments).filter(UsersComments.processed == False).all()

                with db_session.no_autoflush:
                    self.process_and_save_results(db_session, topics, Topics)
                    self.process_and_save_results(db_session, replies, Replies)
                    self.process_and_save_results(db_session, comments, UsersComments)

                db_session.commit()
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
    
    def run(self):
        print("[Debug] Model activated")
        self.predict_and_save()
