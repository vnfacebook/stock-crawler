import os
import pandas as pd
import numpy as np
import datetime
from typing import Any
from google.cloud import bigquery
from src.utils.logger import logger

class BigQueryWriter:
    def __init__(self, project_id: str = None, dataset_id: str = "stock_data"):
        # Lấy project_id từ ENV nếu không truyền vào
        self.project_id = project_id or os.getenv("BIGQUERY_PROJECT_ID")
        self.dataset_id = dataset_id or os.getenv("BIGQUERY_DATASET_ID", "stock_data")
        
        if not self.project_id:
            logger.warning("BIGQUERY_PROJECT_ID is not set. BigQueryWriter may fail if credentials don't provide a default project.")
            
        try:
            self.client = bigquery.Client(project=self.project_id)
            self._ensure_dataset_exists()
        except Exception as e:
            logger.error(f"Failed to initialize BigQuery Client: {e}. Please check GOOGLE_APPLICATION_CREDENTIALS.")
            self.client = None

    def _ensure_dataset_exists(self):
        if not self.client: return
        dataset_ref = f"{self.client.project}.{self.dataset_id}"
        try:
            self.client.get_dataset(dataset_ref)
        except Exception:
            logger.info(f"Dataset {self.dataset_id} not found. Creating it...")
            dataset = bigquery.Dataset(dataset_ref)
            dataset.location = "US"
            self.client.create_dataset(dataset, timeout=30)
            logger.info(f"Created dataset {self.dataset_id}")

    def _sanitize_data(self, data: Any) -> Any:
        if isinstance(data, list):
            return [self._sanitize_data(x) for x in data]
        elif isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, pd.Timestamp):
            return data.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(data, (datetime.datetime, datetime.date)):
            return data.strftime("%Y-%m-%d %H:%M:%S") if isinstance(data, datetime.datetime) else data.strftime("%Y-%m-%d")
        elif pd.isna(data):
            return None
        elif isinstance(data, (np.integer, np.floating)):
            return data.item()
        elif isinstance(data, np.ndarray):
            return [self._sanitize_data(x) for x in data]
        else:
            return data

    def save(self, data: list | dict | pd.DataFrame, table_name: str):
        """
        Lưu danh sách dict, dict đơn lẻ, hoặc DataFrame vào bảng BigQuery.
        """
        if not self.client:
            logger.error("BigQuery client is not initialized. Cannot save data.")
            return

        if not data:
            return

        table_id = f"{self.client.project}.{self.dataset_id}.{table_name}"

        # Cấu hình Load Job: Tự động tạo bảng nếu chưa có, thêm dữ liệu nếu đã có, cho phép thêm cột mới
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            autodetect=True,
            schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION],
        )

        try:
            if isinstance(data, pd.DataFrame):
                if data.empty: return
                job = self.client.load_table_from_dataframe(data, table_id, job_config=job_config)
                job.result()
                logger.info(f"Loaded {len(data)} rows from DataFrame to BigQuery table {table_id}")
            else:
                data_list = [data] if isinstance(data, dict) else data
                if not data_list: return
                
                # Sanitize data for clean JSON serialization
                sanitized_list = self._sanitize_data(data_list)
                
                job = self.client.load_table_from_json(sanitized_list, table_id, job_config=job_config)
                job.result()
                logger.info(f"Loaded {len(sanitized_list)} JSON rows to BigQuery table {table_id}")
        except Exception as e:
            logger.error(f"Failed to load data to BigQuery table {table_id}: {e}")
