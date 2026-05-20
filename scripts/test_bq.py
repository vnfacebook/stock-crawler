import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

from src.storage.bigquery_writer import BigQueryWriter
import datetime

print("--- STARTING DIRECT BIGQUERY UPLOAD TEST ---")
try:
    bq = BigQueryWriter()

    dummy_data = [{
        "symbol": "TEST_DATA",
        "report_year": 2026,
        "revenue": 1000000.0,
        "net_income": 500000.0,
        "eps": 2500.0,
        "pe": 15.5,
        "fetched_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }]

    print("Uploading dummy batch to BigQuery...")
    bq.save(dummy_data, "market_finance_full")
    print("--- UPLOAD COMPLETE ---")
except Exception as e:
    print(f"Error: {e}")
