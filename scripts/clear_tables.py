import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import bigquery
from dotenv import load_dotenv

load_dotenv()

project_id = os.getenv("BIGQUERY_PROJECT_ID")
dataset_id = os.getenv("BIGQUERY_DATASET_ID", "stock_data")

client = bigquery.Client(project=project_id)

for table_name in ["market_finance_full", "market_history_full"]:
    table_id = f"{project_id}.{dataset_id}.{table_name}"
    try:
        client.delete_table(table_id, not_found_ok=True)
        print(f"Deleted table {table_id} if it existed.")
    except Exception as e:
        print(f"Error deleting table {table_id}: {e}")
