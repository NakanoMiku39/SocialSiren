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
        session = self.Session()
        try:
            while True:
                print("[Debug] Model tries to write to database")
                untranslated_topics = session.query(TranslatedTopics).filter(TranslatedTopics.processed == False).all()
                untranslated_replies = session.query(TranslatedReplies).filter(TranslatedReplies.processed == False).all()

                    # Process topics
                for topic in untranslated_topics:
                    predictions = self.model.predict([topic.content])
                    results = self.interpret_predictions(predictions, [topic])
                    for text, label, probability in results:
                        new_result = Result(
                            id=topic.id,
                            content=text,
                            result=f"{label} with probability {probability}",
                            source_type='topic'
                        )
                        session.add(new_result)
                        topic.processed = True

                # Process replies
                for reply in untranslated_replies:
                    predictions = self.model.predict([reply.content])
                    results = self.interpret_predictions(predictions, [reply])
                    for text, label, probability in results:
                        new_result = Result(
                            id=reply.id,
                            content=text,
                            result=f"{label} with probability {probability}",
                            source_type='reply'
                        )
                        session.add(new_result)
                        reply.processed = True
                    
                session.commit()  # Commit all changes
                print("[Debug] Model write successful")
                time.sleep(10)  # Wait before checking for more unprocessed entries
        except Exception as e:
            session.rollback()
            print(f"Error during processing: {e}")
            print("[Debug] Model write failed")
        finally:
            session.close()
            
    def interpret_predictions(self, predictions, items):
        """
        Interpret model predictions to human-readable format.
        Returns a list of tuples with each containing the text, prediction label, and probability.
        """
        probabilities = tf.nn.softmax(predictions, axis=1)
        predicted_indices = tf.argmax(probabilities, axis=1)
        labels = ["Not a Disaster", "Disaster"]
        
        results = []
        for index, item in zip(predicted_indices, items):
            text = item.content  # Extracting text content from the object
            label = labels[index]
            probability = probabilities.numpy()[index, predicted_indices[index]]
            results.append((text, label, f"{probability:.2f}"))
        
        return results

    def run(self):
        """
        Start the continuous prediction process.
        """
        print("[Debug] Model activated")
        self.predict_and_save()


