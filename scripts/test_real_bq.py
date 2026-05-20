import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.crawl_full_market import crawl_full_market

print("--- STARTING REAL CRAWL & BIGQUERY UPLOAD TEST ---")
try:
    # Crawl 3 symbols and save to BigQuery
    crawl_full_market(limit=3)
    print("--- TEST COMPLETE ---")
except Exception as e:
    print(f"Error during crawl: {e}")
