from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import nltk
from nltk.tokenize import sent_tokenize
import time
from class_datatypes import TranslatedTopics, TranslatedReplies, Topics, Replies

class Translator:
    def __init__(self, model_name, Session):
        self.Session = Session
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
        # nltk.download('punkt')
        print("[Debug] Translator initialized")

    def translate_text(self, text, src_lang="zh", tgt_lang="eng_Latn", max_new_tokens=500):
        sentences = sent_tokenize(text)
        translations = []
        for sentence in sentences:
            # Assume `preprocess_text` is defined somewhere in the class or module
            # processed_text = self.preprocess_text(sentence) 
            inputs = self.tokenizer(sentence, return_tensors="pt", padding=True)
            translated_tokens = self.model.generate(
                inputs.input_ids, 
                forced_bos_token_id=self.tokenizer.lang_code_to_id[tgt_lang],
                max_new_tokens=max_new_tokens
            )
            translated_text = self.tokenizer.decode(translated_tokens[0], skip_special_tokens=True)
            translations.append(translated_text)
        return " ".join(translations)

    def translate_database_contents(self):
        db_session = self.Session()
        # 查询所有未翻译的Topics
        print("[Debug] Translator tries to write to database")
        try:
            with db_session.no_autoflush:
                untranslated_topics = db_session.query(Topics).filter(Topics.processed == False).all()
                untranslated_replies = db_session.query(Replies).filter(Replies.processed == False).all()

                for topic in untranslated_topics:
                    # print("[Debug] Translating a topic")
                    translated_content = self.translate_text(topic.content)
                    translated_topic = TranslatedTopics(id=topic.id, content=translated_content, date_time=topic.date_time)
                    db_session.add(translated_topic)
                    topic.processed = True

                # 查询所有未翻译的Replies
                for reply in untranslated_replies:
                    # print("[Debug] Translating a reply")
                    translated_content = self.translate_text(reply.content)
                    translated_reply = TranslatedReplies(id=reply.id, content=translated_content, date_time=reply.date_time, topic_id=reply.topic_id)
                    db_session.add(translated_reply)
                    reply.processed = True

            # 尝试提交所有翻译到数据库
            db_session.commit()
            print("[Debug] Translator write successful")
        except Exception as e:
            # 如果出现异常，进行回滚
            print("[Debug] Translator write failed")
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def run(self):
        print("[Debug] Translator activated")
        while True:
            print("[Debug] Translator begins a new translating round")
            self.translate_database_contents()
            time.sleep(10)  # Adjust this sleep time as necessary for your application
    
    def __del__(self):
            """资源清理"""
            self.Session.remove()  # 关闭 session
