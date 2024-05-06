import time
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import pandas as pd
import tensorflow as tf
import keras_nlp
from sklearn.model_selection import train_test_split
from class_datatypes import TranslatedTopics, TranslatedReplies, Result
from transformers import BertTokenizer

class DisasterTweetModel:
    def __init__(self, train_path, test_path, Session, preset='distil_bert_base_en_uncased', sequence_length=160):
        """
        Initialize the model, its preprocessor, load datasets, and setup database connection.
        """
        self.train_path = train_path
        self.test_path = test_path
        self.Session = Session
        self.preset = preset
        self.sequence_length = sequence_length
        self.preprocessor = keras_nlp.models.DistilBertPreprocessor.from_preset(
            self.preset, sequence_length=self.sequence_length)        
        self.model = tf.keras.models.load_model('model/disaster_tweet_model.keras')
        self.df_train = pd.read_csv(train_path)
        self.df_test = pd.read_csv(test_path)
        print("[Debug] Model initialized")

    def __del__(self):
        """
        Close database connection when the instance is destroyed.
        """
        self.Session.remove()  # 关闭 session

    def predict_and_save(self):
        """
        Continuously predict and save results from new translated topics and replies.
        """
        db_session = self.Session()
        try:
            while True:
                print("[Debug] Model tries to write to database")
                untranslated_topics = db_session.query(TranslatedTopics).filter(TranslatedTopics.processed == False).all()
                untranslated_replies = db_session.query(TranslatedReplies).filter(TranslatedReplies.processed == False).all()

             # Process topics
                for topic in untranslated_topics:
                    predictions = self.model.predict([topic.content])
                    results = self.interpret_predictions(predictions, [topic.content])
                    for text, label, probability in results:
                        new_result = Result(
                            source_id=topic.id,
                            content=text,
                            date_time=topic.date_time,
                            is_disaster=label,
                            probability=probability,
                            source_type='topic'
                        )
                        db_session.add(new_result)
                        topic.processed = True

                # Process replies
                for reply in untranslated_replies:
                    predictions = self.model.predict([reply.content])
                    results = self.interpret_predictions(predictions, [reply.content])
                    for text, label, probability in results:
                        new_result = Result(
                            source_id=reply.id,
                            content=text,
                            date_time=reply.date_time,
                            is_disaster=label,
                            probability=probability,
                            source_type='reply'
                        )
                        db_session.add(new_result)
                        reply.processed = True    
                                        
                db_session.commit()  # Commit all changes
                print("[Debug] Model write successful")
                time.sleep(10)  # Wait before checking for more unprocessed entries
        except Exception as e:
            db_session.rollback()
            print(f"Error during processing: {e}")
            print("[Debug] Model write failed")
        finally:
            db_session.close()
            
    def interpret_predictions(self, predictions, items):
        """
        Interpret model predictions to human-readable format.
        Returns a list of tuples with each containing the text, prediction label, and probability.
        """
        probabilities = tf.nn.softmax(predictions, axis=1)
        predicted_indices = tf.argmax(probabilities, axis=1)
        labels = ["Not a Disaster", "Disaster"]
        
        results = []
        for text, index in zip(items, predicted_indices):
            label = bool(index)  # 将index转换为布尔值，假设'class 1'为灾害
            probability = probabilities[:, index][0]  # Get the probability for the predicted class
            results.append((text, label, float(probability)))
            
        return results

    def run(self):
        """
        Start the continuous prediction process.
        """
        print("[Debug] Model activated")
        self.predict_and_save()


