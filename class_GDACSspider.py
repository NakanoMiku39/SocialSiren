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
        self.driver = webdriver.Chrome(options=options)          
        self.driver.get("https://www.gdacs.org/Alerts/default.aspx")

    def start_download(self):
        """Set level to 'All', start the search and initiate download."""
        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "inputAlert"))
        ).send_keys('All;Orange;Red;Green')

        WebDriverWait(self.driver, 20).until(
            EC.element_to_be_clickable((By.ID, "btnsearch"))
        ).click()

        time.sleep(10)  # Wait for results to process
        self.driver.execute_script("downloadResult();")
        time.sleep(10)  # Wait for the download to complete

    def process_file(self):
        """Wait for the file to appear and process it."""
        geojson_file_path = os.path.join(self.download_dir, "result.geojson")
        while not os.path.exists(geojson_file_path):
            time.sleep(1)

        print(f"[Debug] Found file: {geojson_file_path}")

        with open(geojson_file_path, 'r', encoding='utf-8') as file:
            data = file.read()
            print(f"[Debug] Raw file content: {data[:500]}")  # 打印文件内容的前500个字符进行调试

        try:
            data = json.loads(data)
            print(f"[Debug] Parsed data type: {type(data)}")
        except json.JSONDecodeError as e:
            print(f"[Debug] JSON decode error: {e}")
            return

        if not isinstance(data, dict):
            print("[Debug] Data is not a dictionary, aborting process.")
            return

        self.store_data(data)
        self.manage_file(geojson_file_path)

    def validate_and_parse_date(self, date_str):
        # Regex to match ISO 8601 date-time format
        date_pattern = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}'
        if re.match(date_pattern, date_str):
            return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        else:
            raise ValueError("Date format is incorrect or missing")
    
    def store_data(self, data):
        """Insert data into SQLite database."""
        db_session = self.Session()
        try:
            for feature in data.get('features', []):
                properties = feature.get('properties', {})
                eventid = properties.get('eventid', 'Unknown')
                description = properties.get('description', 'Unknown')
                country = properties.get('country', 'Unknown')
                todate_str = properties.get('todate', '1970-01-01T00:00:00')
                todate = self.validate_and_parse_date(todate_str)
                print(f"[Debug] One entry: {eventid}, {description}, {country}, {todate}")
                
                # Check if the entry already exists
                existing_entry = db_session.query(GDACS).filter_by(id=eventid).first()
                if existing_entry is None:
                    with db_session.no_autoflush:
                        new_gdacs = GDACS(id=eventid, content=description, date_time=todate, location=country)
                        with db_lock:
                            db_session.add(new_gdacs)
                    print(f"[Debug] Added new entry: {eventid}, {description}, {country}, {todate}")
                else:
                    print(f"[Debug] Entry already exists, skipping: {eventid}")  
                              
            self.retry_on_lock(db_session)
        except Exception as e:
            # 如果出现异常，进行回滚
            print("[Debug] GDACS write failed")
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
        """Rename and move the processed file."""
        new_file_name = f"processed_{int(time.time())}.geojson"
        os.rename(file_path, os.path.join(self.processed_dir, new_file_name))

    def run(self):
        """Execute the web scraping process."""
        print("[Debug] GDACS Spider activated")    
        self.start_download()
        self.process_file()

    def stop(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
        print("WebDriver quit successfully")

    def __del__(self):
        """Clean up resources."""
        self.Session.remove()
        if self.driver:
            self.driver.quit()
        print("WebDriver quit successfully")
