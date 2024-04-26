import sqlite3
import pandas as pd
import tensorflow as tf
import keras_nlp
from sklearn.model_selection import train_test_split

class DisasterTweetModel:
    def __init__(self, train_path, test_path, db_path, preset='distil_bert_base_en_uncased', sequence_length=160):
        """
        Initialize the model, its preprocessor, load datasets, and setup database connection.
        """
        self.train_path = train_path
        self.test_path = test_path
        self.db_path = db_path
        self.preset = preset
        self.sequence_length = sequence_length
        self.preprocessor = keras_nlp.models.DistilBertPreprocessor.from_preset(preset, sequence_length=sequence_length)
        self.model = keras_nlp.models.DistilBertClassifier.from_preset(preset, preprocessor=self.preprocessor, num_classes=2)
        self.df_train = pd.read_csv(train_path)
        self.df_test = pd.read_csv(test_path)
        self.conn = sqlite3.connect(self.db_path)
        
    def __del__(self):
        """
        Close database connection when the instance is destroyed.
        """
        self.conn.close()

    def train(self, batch_size=32, epochs=2):
        """
        Train the model using the loaded training dataset.
        """
        X = self.df_train["text"]
        y = self.df_train["target"]
        X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)
        
        self.model.compile(
            loss=tf.keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            optimizer=tf.keras.optimizers.Adam(1e-5),
            metrics=["accuracy"]
        )
        
        history = self.model.fit(
            x=X_train,
            y=y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_data=(X_val, y_val)
        )
        return history

    def save_model(self, file_path):
        """
        Save the model to a specified file path with .keras extension.
        """
        if not file_path.endswith('.keras'):
            file_path += '.keras'
        self.model.save(file_path)

    def load_model(self, file_path):
        """
        Load a model from a specified file path.
        """
        self.model = tf.keras.models.load_model(file_path)

    def predict(self, texts):
        """
        Predict using the loaded model. This method assumes that texts are directly consumable by the model.
        """
        # Preprocess texts to get the correct model input format
        processed_texts = self.preprocessor(texts)
        # Since `processed_texts` now contains a dictionary suitable for the model, it should be passed directly.
        predictions = self.model(processed_texts)  # Using the dictionary directly if the model expects it
        return predictions
    
    def save_results_to_db(self, tweets, results):
        """
        Save the prediction results along with the tweets into the SQLite database.
        """
        cursor = self.conn.cursor()
        for tweet, result in zip(tweets, results):
            cursor.execute('''
                INSERT INTO tweet_results (tweet, result)
                VALUES (?, ?)
            ''', (tweet, result))
        self.conn.commit()

    def interpret_predictions(self, predictions, tweets):
        """
        Interpret model predictions to human-readable format and save to database.
        """
        probabilities = tf.nn.softmax(predictions, axis=1)
        predicted_indices = tf.argmax(probabilities, axis=1)
        labels = ["Not a Disaster", "Disaster"]
        predicted_labels = [labels[index] for index in predicted_indices.numpy()]
        
        results = []
        for tweet, label, probability in zip(tweets, predicted_labels, probabilities.numpy()):
            result = f"{tweet}: {label}, Probabilities: {probability}"
            results.append(result)
        
        self.save_results_to_db(tweets, results)
        return results

# Example usage:
db_path = 'result.db'
train_path = 'dataset/train.csv'
test_path = 'dataset/test.csv'
model = DisasterTweetModel(train_path, test_path, db_path)
model.load_model('model/disaster_tweet_model.keras')
predictions = model.predict(["Sample tweet to predict disaster", "Im on fire", "there is no earthquake today", "tornado coming tomorrow"])
interpreted_results = model.interpret_predictions(predictions, ["Sample tweet to predict disaster", "Im on fire", "there is no earthquake today", "tornado coming tomorrow"])
for result in interpreted_results:
    print(result)