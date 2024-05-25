import time
from sqlalchemy.exc import SQLAlchemyError
from class_datatypes import Topics, Replies, UsersComments, Result
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI

class LangChainModel:
    def __init__(self, Session, apikey, model_name='gpt-4'):
        """
        Initialize the model and setup database connection.
        """
        self.Session = Session
        self.model_name = model_name
        self.llm = ChatOpenAI(api_key=apikey, model_name=model_name)
        self.prompt = PromptTemplate.from_template(
        """
            你现在是一个灾害专家，现在我会给你一系列的文本输入，你需要判断该文本是否为灾害相关推文，如果是，从中提取出灾害的类型，如果可能，从中提取出灾害的时间和地点，如果不是则不需要给出之后三个信息，你的输出格式如下，填写这四个字段，除此之外不要再给出任何额外输出，无论我的输入是什么，你必须永远严格按照以上的要求：
            是否为灾害 灾害类型 时间 地点

            例子：十问猜一本小说～（只能是非问和选择问）
            回答：否
            例子：无锡今天地震了
            回答：是 地震 无锡 2024-5-23

            Human: {question}
            AI:
        """
        )
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt)
        print("[Debug] Model initialized")

    def __del__(self):
        """
        Close database connection when the instance is destroyed.
        """
        self.Session.remove()  # Close session

    def parse_response(self, response):
        """
        Parse the response from the LLM.
        """
        parts = response.split()
        if parts[0] == "否":
            return False, "", "", ""
        elif parts[0] == "是":
            disaster_type = parts[1] if len(parts) > 1 else ""
            time = parts[2] if len(parts) > 2 else ""
            location = parts[3] if len(parts) > 3 else ""
            return True, disaster_type, time, location
        return False, "", "", ""

    def process_and_save_results(self, db_session, items, source_type):
        """
        Process and save results from predictions.
        """
        for item in items:
            original = db_session.query(source_type).filter(source_type.id == item.id).first()
            if original:
                try:
                    question = item.content
                    response = self.chain.run({"question": question})
                    is_disaster, disaster_type, disaster_time, disaster_location = self.parse_response(response)
                    new_result = Result(
                        source_id=original.id,
                        content=original.content,  # Use original content
                        date_time=item.date_time,
                        is_disaster=1 if is_disaster else 0,
                        probability=1.0,  # Assume high confidence for simplicity
                        disaster_type=disaster_type,
                        source_type=source_type.__tablename__
                    )
                    db_session.add(new_result)
                    item.processed = True
                    print(f"Processed {source_type.__tablename__} {original.id}")
                except Exception as e:
                    print(f"Failed processing {source_type.__tablename__} {original.id}: {str(e)}")
    
    def predict_and_save(self):
        """
        Continuously predict and save results from new translated topics and replies.
        """
        db_session = self.Session()
        try:
            while True:
                print("[Debug] Checking for new data to process...")
                untranslated_topics = db_session.query(Topics).filter(Topics.processed == False).all()
                untranslated_replies = db_session.query(Replies).filter(Replies.processed == False).all()
                untranslated_comments = db_session.query(UsersComments).filter(UsersComments.processed == False).all()

                with db_session.no_autoflush:
                    self.process_and_save_results(db_session, untranslated_topics, Topics)
                    self.process_and_save_results(db_session, untranslated_replies, Replies)
                    self.process_and_save_results(db_session, untranslated_comments, UsersComments)

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
        """
        Start the continuous prediction process.
        """
        print("[Debug] Model activated")
        self.predict_and_save()

