from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import sqlite3
import json
import os
import time
from class_datatypes import GDACS
from datetime import datetime
import re
from sqlalchemy.exc import OperationalError
from lock import db_lock

class GDACSSpider:
    def __init__(self, download_dir, processed_dir, Session, options):
        self.download_dir = download_dir
        self.processed_dir = processed_dir
        self.Session = Session
        self.driver = None
        self.initialize_driver(options)
        print("[Debug] GDACS Spider initialized")

    def initialize_driver(self, options):
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.get("https://www.gdacs.org/Alerts/default.aspx")
        except Exception as e:
            print(f"[Error] Failed to initialize WebDriver: {e}")
            self.clean_up()
            raise e

    def start_download(self):
        try:
            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "inputAlert"))
            ).send_keys('All;Orange;Red;Green')

            WebDriverWait(self.driver, 20).until(
                EC.element_to_be_clickable((By.ID, "btnsearch"))
            ).click()

            time.sleep(10)  # Wait for results to process
            self.driver.execute_script("downloadResult();")
            time.sleep(10)  # Wait for the download to complete
        except Exception as e:
            print(f"[Error] Failed to start download: {e}")
            self.clean_up()
            raise e

    def process_file(self):
        geojson_file_path = os.path.join(self.download_dir, "result.geojson")
        while not os.path.exists(geojson_file_path):
            time.sleep(1)

        with open(geojson_file_path, 'r', encoding='utf-8') as file:
            data = file.read()

        try:
            data = json.loads(data)
        except json.JSONDecodeError as e:
            print(f"[Debug] JSON decode error: {e}")
            return

        if not isinstance(data, dict):
            print("[Debug] Data is not a dictionary, aborting process.")
            return

        self.store_data(data)
        self.manage_file(geojson_file_path)

    def validate_and_parse_date(self, date_str):
        date_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        if re.match(date_pattern, date_str):
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        else:
            raise ValueError("Date format is incorrect or missing")

    def store_data(self, data):
        db_session = self.Session()
        try:
            for feature in data.get('features', []):
                properties = feature.get('properties', {})
                eventid = properties.get('eventid', 'Unknown')
                description = properties.get('description', 'Unknown')
                country = properties.get('country', 'Unknown')
                todate_str = properties.get('todate', '1970-01-01T00:00:00')
                todate = self.validate_and_parse_date(todate_str)

                existing_entry = db_session.query(GDACS).filter_by(id=eventid).first()
                if existing_entry is None:
                    with db_session.no_autoflush:
                        new_gdacs = GDACS(id=eventid, content=description, date_time=todate, location=country)
                        with db_lock:
                            db_session.add(new_gdacs)
                else:
                    print(f"[Debug] Entry already exists, skipping: {eventid}")

            self.retry_on_lock(db_session)
        except Exception as e:
            db_session.rollback()
            raise e
        finally:
            db_session.close()

    def retry_on_lock(self, session, max_retries=5, wait_time=1):
        retries = 0
        while retries < max_retries:
            try:
                with session.no_autoflush:
                    with db_lock:
                        session.commit()
                print("[Debug] GDACS write successful")
                break
            except OperationalError as e:
                if "database is locked" in str(e):
                    retries += 1
                    print("[Debug] Database is locked, retrying...")
                    time.sleep(wait_time)
                else:
                    raise

    def manage_file(self, file_path):
        new_file_name = f"processed_{int(time.time())}.geojson"
        os.rename(file_path, os.path.join(self.processed_dir, new_file_name))

    def run(self):
        print("[Debug] GDACS Spider activated")
        try:
            self.start_download()
            self.process_file()
        except Exception as e:
            print(f"[Error] GDACS run failed: {e}")
            self.clean_up()
            raise e

    def stop(self):
        self.clean_up()

    def __del__(self):
        self.clean_up()

    def clean_up(self):
        if self.driver:
            self.driver.quit()
        self.Session.remove()
        print("Resources cleaned up successfully")
