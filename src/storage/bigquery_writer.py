import os
import pandas as pd
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

    def save(self, data: list | dict | pd.DataFrame, table_name: str):
        """
        Lưu danh sách dict, dict đơn lẻ, hoặc DataFrame vào bảng BigQuery.
        """
        if not self.client:
            logger.error("BigQuery client is not initialized. Cannot save data.")
            return

        if not data:
            return

        # Chuyển đổi sang DataFrame nếu cần
        if isinstance(data, pd.DataFrame):
            df = data
        elif isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)

        if df.empty:
            return

        table_id = f"{self.client.project}.{self.dataset_id}.{table_name}"

        # Cấu hình Load Job: Tự động tạo bảng nếu chưa có, thêm dữ liệu nếu đã có
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_APPEND",
            autodetect=True,
        )

        try:
            job = self.client.load_table_from_dataframe(df, table_id, job_config=job_config)
            job.result()  # Đợi job hoàn thành
            logger.info(f"Loaded {len(df)} rows to BigQuery table {table_id}")
        except Exception as e:
            logger.error(f"Failed to load data to BigQuery table {table_id}: {e}")
