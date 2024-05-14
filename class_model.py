import pandas as pd
import tensorflow as tf
import joblib
from transformers import DistilBertTokenizer, TFDistilBertForSequenceClassification
from sklearn.preprocessing import LabelEncoder
from class_datatypes import Topics, Replies, UsersComments, TranslatedTopics, TranslatedReplies, TranslatedUsersComments, Result
import time

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
        self.df_train = pd.read_csv(train_path)
        self.df_test = pd.read_csv(test_path)
        print("[Debug] Model initialized")
        print(self.label_encoder.classes_)

    def __del__(self):
        """
        Close database connection when the instance is destroyed.
        """
        self.Session.remove()  # 关闭 session

    def predict_and_save(self):
        """
        Continuously predict and save results from new translated topics and replies,
        but use the content from the original Topics and Replies for saving in the results.
        """
        db_session = self.Session()
        try:
            while True:
                print("[Debug] Model tries to write to database")
                untranslated_topics = db_session.query(TranslatedTopics).filter(TranslatedTopics.processed == False).all()
                untranslated_replies = db_session.query(TranslatedReplies).filter(TranslatedReplies.processed == False).all()
                untranslated_comments = db_session.query(TranslatedUsersComments).filter(TranslatedUsersComments.processed == False).all()

                with db_session.no_autoflush:
                    # Process topics
                    for trans_topic in untranslated_topics:
                        original_topic = db_session.query(Topics).filter(Topics.id == trans_topic.id).first()  # Assuming there is a reference to the original topic
                        if original_topic:
                            encoded_text = self.encode_texts([trans_topic.content])
                            predictions = self.model.predict(encoded_text)
                            results = self.interpret_predictions(predictions, [trans_topic.content])
                            for _, label, probability, disaster_type in results:
                                new_result = Result(
                                    source_id=original_topic.id,
                                    content=original_topic.content,  # Use original content
                                    date_time=trans_topic.date_time,
                                    is_disaster=label,
                                    probability=probability,
                                    disaster_type=disaster_type,
                                    source_type='topic'
                                )
                                db_session.add(new_result)
                                trans_topic.processed = True

                    # Process replies
                    for trans_reply in untranslated_replies:
                        original_reply = db_session.query(Replies).filter(Replies.id == trans_reply.id).first()  # Assuming there is a reference to the original reply
                        if original_reply:
                            encoded_text = self.encode_texts([trans_reply.content])
                            predictions = self.model.predict(encoded_text)
                            results = self.interpret_predictions(predictions, [trans_reply.content])
                            for _, label, probability, disaster_type in results:
                                new_result = Result(
                                    source_id=original_reply.id,
                                    content=original_reply.content,  # Use original content
                                    date_time=trans_reply.date_time,
                                    is_disaster=label,
                                    probability=probability,
                                    disaster_type=disaster_type,
                                    source_type='reply'
                                )
                                db_session.add(new_result)
                                trans_reply.processed = True    
                                
                    # Process comments
                    for trans_comment in untranslated_comments:
                        original_comment = db_session.query(UsersComments).filter(UsersComments.id == trans_comment.id).first()  # Assuming there is a reference to the original reply
                        if original_comment:
                            encoded_text = self.encode_texts([trans_comment.content])
                            predictions = self.model.predict(encoded_text)
                            results = self.interpret_predictions(predictions, [trans_comment.content])
                            for _, label, probability, disaster_type in results:
                                new_result = Result(
                                    source_id=original_comment.id,
                                    content=original_comment.content,  # Use original content
                                    date_time=trans_comment.date_time,
                                    is_disaster=label,
                                    probability=probability,
                                    disaster_type=disaster_type,
                                    source_type='comment'
                                )
                                db_session.add(new_result)
                                trans_comment.processed = True    

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
        If an index is out of bounds, assume the tweet is not a disaster.
        """
        DISASTER_THRESHOLD = 0.8  # Define a probability threshold for disaster
        probabilities = tf.nn.softmax(predictions.logits, axis=1)
        predicted_indices = tf.argmax(probabilities, axis=1)
        predicted_labels = self.label_encoder.inverse_transform(predicted_indices.numpy())

        results = []
        for i, (text, predicted_label) in enumerate(zip(items, predicted_labels)):
            # Ensure the index is within the valid range of probabilities
            if predicted_indices[i] < probabilities.shape[1]:
                probability = probabilities[i, predicted_indices[i]].numpy()
                is_disaster = 1 if probability > DISASTER_THRESHOLD else 0
                results.append((text, is_disaster, float(probability), predicted_label))
            else:
                # Handle out of bounds by assuming not a disaster
                print(f"[Warning] Index {predicted_indices[i]} out of bounds for probabilities with shape {probabilities.shape}. Assuming not a disaster.")
                results.append((text, 0, 0.0, "Not a Disaster"))  # Assume not a disaster in case of out-of-bounds

        return results

    def encode_texts(self, texts):
        """
        Encode texts for prediction.
        """
        return [self.tokenizer.encode(text, add_special_tokens=True, max_length=self.sequence_length, truncation=True, padding='max_length') for text in texts]
    
    def run(self):
        """
        Start the continuous prediction process.
        """
        print("[Debug] Model activated")
        self.predict_and_save()


