from class_datatypes import Result, GDACS
from sqlalchemy import desc, asc, Boolean

class DataManager:
    def __init__(self, Session):
        self.Session = Session
        print("[Debug] DataManager initialized")

    def get_data(self, filters=None, order_by=None, order_desc=True):
        db_session = self.Session()
        try:
            query = db_session.query(Result)
            if filters:
                for key, value in filters.items():
                    if hasattr(Result, key) and value is not None:
                        field = getattr(Result, key)
                        # Check for the condition where filter is not specifying a single type
                        if value == 'all':  # Assuming 'all' is used in the frontend to indicate no specific filter
                            continue
                        if isinstance(field.type, Boolean) and isinstance(value, str):
                            value = value.lower() in ['true', '1', 'yes']  # Convert string to boolean for SQLAlachemy
                        query = query.filter(field == value)
            if order_by and hasattr(Result, order_by):
                order_function = desc if order_desc else asc
                query = query.order_by(order_function(getattr(Result, order_by)))
            return query.all()
        except Exception as e:
            print(f"Error during processing: {e}")
            print("[Debug] Model write failed")
        finally:
            db_session.close()

    def get_data_gdacs(self, order_by=None, order_desc=True):
        db_session = self.Session()
        try:
            query = db_session.query(GDACS)
            # Apply sorting if the attribute exists in GDACS
            if order_by and hasattr(GDACS, order_by):
                order_function = desc if order_desc else asc
                query = query.order_by(order_function(getattr(GDACS, order_by)))

            return query.all()
        except Exception as e:
            print(f"Error during processing: {e}")
            return []
        finally:
            db_session.close()
