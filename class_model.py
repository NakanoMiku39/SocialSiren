import pandas as pd
import tensorflow as tf
import joblib
from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
from sklearn.preprocessing import LabelEncoder
from class_datatypes import Topics, Replies, UsersComments, TranslatedTopics, TranslatedReplies, TranslatedUsersComments, Result
import time
from sqlalchemy.exc import SQLAlchemyError
from lock import db_lock

class DisasterTweetModel:
    def __init__(self, train_path, test_path, Session, model_path='model/distilbert_disaster_model', sequence_length=128):
        """
        Initialize the model, its preprocessor, load datasets, and setup database connection.
        """
        self.train_path = train_path
        self.test_path = test_path
        self.Session = Session
        self.model_path = model_path
        self.sequence_length = sequence_length
        self.tokenizer = DistilBertTokenizer.from_pretrained('distilbert-base-uncased')
        self.model = TFDistilBertForSequenceClassification.from_pretrained(self.model_path)
        self.label_encoder = joblib.load('model/keyword_encoder.pkl')  # Assume encoder is saved here
        # self.label_encoder.classes_ = [label.replace('%20', ' ') for label in self.label_encoder.classes_]
        self.df_train = pd.read_csv(train_path)
        self.df_test = pd.read_csv(test_path)
        print("[Debug] Model initialized")
        print(self.label_encoder.classes_)

    def __del__(self):
        """
        Close database connection when the instance is destroyed.
        """
        self.Session.remove()  # 关闭 session

    def encode_texts(self, texts):
        """
        Encode texts for prediction.
        """
        return [self.tokenizer.encode(text, add_special_tokens=True, max_length=self.sequence_length, truncation=True, padding='max_length') for text in texts]

    def interpret_predictions(self, predictions, items):
        results = []
        try:
            probabilities = tf.nn.softmax(predictions.logits, axis=1)
            predicted_indices = tf.argmax(probabilities, axis=1).numpy()

            # Debugging output to check index validity before decoding
            print(f"[Debug] Label encoder classes count: {len(self.label_encoder.classes_)}")

            for i, (text, predicted_index) in enumerate(zip(items, predicted_indices)):
                print(f"[Debug] Text={text}, Predicted Index={predicted_index}")

                if predicted_index >= len(self.label_encoder.classes_):
                    print(f"[Error] Predicted index {predicted_index} is out of bounds for label encoder classes.")
                    results.append((text, 0, 0.0, "Not a Disaster"))
                    continue

                probability = probabilities[i, predicted_index].numpy()
                is_disaster = 1 if probability > 0.8 else 0
                predicted_label = self.label_encoder.inverse_transform([predicted_index])[0]
                results.append((text, is_disaster, float(probability), predicted_label))
                
                print(f"[Debug] Processed: Label={predicted_label}, Probability={probability}")

        except Exception as e:
            print(f"[Exception] Error during interpretation: {str(e)}")
            for text in items[len(results):]:
                results.append((text, 0, 0.0, "Not a Disaster"))

        return results
    
    def process_and_save_results(self, db_session, items, source_type):
        """
        Process and save results from predictions, convert %20 to space in labels before saving.
        """
        for item in items:
            original = db_session.query(source_type).filter(source_type.id == item.id).first()
            if original:
                try:
                    encoded_text = self.encode_texts([item.content])
                    predictions = self.model.predict(encoded_text)
                    results = self.interpret_predictions(predictions, [item.content])
                    for _, label, probability, disaster_type in results:
                        # Convert %20 to space in the disaster_type label before saving
                        disaster_type = disaster_type.replace('%20', ' ')
                        new_result = Result(
                            source_id=original.id,
                            content=original.content,  # Use original content
                            date_time=item.date_time,
                            is_disaster=label,
                            probability=probability,
                            disaster_type=disaster_type,  # Saved with converted label
                            source_type=source_type.__tablename__
                        )
                        with db_lock:
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
                untranslated_topics = db_session.query(TranslatedTopics).filter(TranslatedTopics.processed == False).all()
                untranslated_replies = db_session.query(TranslatedReplies).filter(TranslatedReplies.processed == False).all()
                untranslated_comments = db_session.query(TranslatedUsersComments).filter(TranslatedUsersComments.processed == False).all()

                with db_session.no_autoflush:
                    self.process_and_save_results(db_session, untranslated_topics, Topics)
                    self.process_and_save_results(db_session, untranslated_replies, Replies)
                    self.process_and_save_results(db_session, untranslated_comments, UsersComments)
                    with db_lock:
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


