import pytest
import datetime
import pandas as pd
import numpy as np
from unittest.mock import MagicMock, patch
from src.storage.bigquery_writer import BigQueryWriter

@pytest.fixture
def mock_bigquery_client():
    """
    Mock cho google.cloud.bigquery.Client
    """
    with patch("google.cloud.bigquery.Client") as mock_client_cls:
        mock_client = MagicMock()
        mock_client.project = "test-project"
        mock_client_cls.return_value = mock_client
        yield mock_client

def test_bigquery_writer_init(mock_bigquery_client):
    """
    Test khởi tạo BigQueryWriter và tự động tạo dataset nếu chưa tồn tại.
    """
    writer = BigQueryWriter(project_id="test-project", dataset_id="test_dataset")
    
    assert writer.project_id == "test-project"
    assert writer.dataset_id == "test_dataset"
    assert writer.client == mock_bigquery_client
    
    # Kiểm tra xem get_dataset có được gọi để kiểm tra sự tồn tại của dataset không
    mock_bigquery_client.get_dataset.assert_called_once_with("test-project.test_dataset")

def test_bigquery_writer_sanitize_data():
    """
    Test hàm _sanitize_data chuyển đổi dữ liệu đặc thù của Pandas/Numpy
    về kiểu dữ liệu Python cơ bản hỗ trợ JSON serialization.
    """
    # Khởi tạo mock client để tránh lỗi kết nối trong constructor
    with patch("google.cloud.bigquery.Client") as mock_client_cls:
        writer = BigQueryWriter(project_id="test-project", dataset_id="test_dataset")
        
        # 1. Test Pandas Timestamp -> string
        ts = pd.Timestamp("2026-05-21 10:00:00")
        assert writer._sanitize_data(ts) == "2026-05-21 10:00:00"
        
        # 2. Test datetime.datetime -> string
        dt = datetime.datetime(2026, 5, 21, 10, 0, 0)
        assert writer._sanitize_data(dt) == "2026-05-21 10:00:00"
        
        # 3. Test datetime.date -> string
        d = datetime.date(2026, 5, 21)
        assert writer._sanitize_data(d) == "2026-05-21"
        
        # 4. Test NaN / NaT / None -> None
        assert writer._sanitize_data(np.nan) is None
        assert writer._sanitize_data(pd.NA) is None
        
        # 5. Test Numpy numeric -> Python float/int
        np_int = np.int64(42)
        np_float = np.float64(3.14)
        assert writer._sanitize_data(np_int) == 42
        assert isinstance(writer._sanitize_data(np_int), int)
        assert writer._sanitize_data(np_float) == 3.14
        assert isinstance(writer._sanitize_data(np_float), float)
        
        # 6. Test Đệ quy trong list và dict
        complex_data = {
            "symbol": "FPT",
            "date": datetime.date(2026, 5, 21),
            "indicators": [np.nan, np.float64(15.5), {"nested_time": pd.Timestamp("2026-05-21 12:00:00")}]
        }
        sanitized = writer._sanitize_data(complex_data)
        
        assert sanitized["symbol"] == "FPT"
        assert sanitized["date"] == "2026-05-21"
        assert sanitized["indicators"][0] is None
        assert sanitized["indicators"][1] == 15.5
        assert isinstance(sanitized["indicators"][1], float)
        assert sanitized["indicators"][2]["nested_time"] == "2026-05-21 12:00:00"

def test_bigquery_writer_save_dict(mock_bigquery_client):
    """
    Test ghi dữ liệu dạng dict/list thông qua load_table_from_json.
    """
    writer = BigQueryWriter(project_id="test-project", dataset_id="test_dataset")
    
    # Mock load job
    mock_job = MagicMock()
    mock_bigquery_client.load_table_from_json.return_value = mock_job
    
    data = {"symbol": "FPT", "price": 95.5}
    writer.save(data, "daily_prices")
    
    # Kiểm tra load_table_from_json được gọi đúng cách
    mock_bigquery_client.load_table_from_json.assert_called_once()
    args, kwargs = mock_bigquery_client.load_table_from_json.call_args
    
    # Dữ liệu truyền vào đã được làm sạch và bao bọc trong một mảng
    assert args[0] == [{"symbol": "FPT", "price": 95.5}]
    assert args[1] == "test-project.test_dataset.daily_prices"
    
    # Kiểm tra cấu hình LoadJobConfig
    job_config = kwargs.get("job_config")
    assert job_config is not None
    assert job_config.write_disposition == "WRITE_APPEND"
    assert job_config.autodetect is True
    # Kiểm tra SchemaUpdateOption
    from google.cloud import bigquery
    assert bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION in job_config.schema_update_options

def test_bigquery_writer_save_dataframe(mock_bigquery_client):
    """
    Test ghi dữ liệu dạng DataFrame thông qua load_table_from_dataframe.
    """
    writer = BigQueryWriter(project_id="test-project", dataset_id="test_dataset")
    
    mock_job = MagicMock()
    mock_bigquery_client.load_table_from_dataframe.return_value = mock_job
    
    df = pd.DataFrame([{"symbol": "VNM", "price": 68.2}])
    writer.save(df, "daily_prices")
    
    mock_bigquery_client.load_table_from_dataframe.assert_called_once()
    args, kwargs = mock_bigquery_client.load_table_from_dataframe.call_args
    
    assert isinstance(args[0], pd.DataFrame)
    assert args[0].loc[0, "symbol"] == "VNM"
    assert args[1] == "test-project.test_dataset.daily_prices"
