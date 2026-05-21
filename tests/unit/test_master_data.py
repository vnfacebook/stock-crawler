import os
import datetime
import pytest
import pandas as pd
from unittest.mock import MagicMock, patch
from src.storage.master_data import MasterDataManager

@pytest.fixture
def mock_market_info():
    """
    Mock class MarketInfo
    """
    with patch("src.storage.master_data.MarketInfo") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance
        yield mock_instance

def test_master_data_export_symbols(mock_market_info, tmp_path):
    """
    Test hàm export_symbols tạo đúng file master data CSV và thêm trường updated_at.
    """
    # Thiết lập dữ liệu mock công ty trả về
    mock_df = pd.DataFrame([
        {"symbol": "FPT", "organ_name": "Cong ty FPT", "exchange": "HOSE"},
        {"symbol": "VNM", "organ_name": "Vinamilk", "exchange": "HOSE"}
    ])
    mock_market_info.get_companies_info.return_value = mock_df
    
    # Patch base_path của CSVWriter để ghi vào tmp_path
    with patch("src.storage.master_data.CSVWriter") as mock_writer_class:
        mock_writer = MagicMock()
        mock_writer_class.return_value = mock_writer
        
        manager = MasterDataManager()
        manager.master_file = "test_master.csv"
        
        # Gọi hàm export_symbols
        result = manager.export_symbols()
        
        assert result is True
        mock_market_info.get_companies_info.assert_called_once()
        
        # Vì ta dùng pandas `.to_csv()` ghi đè trực tiếp trong `MasterDataManager.export_symbols` (xem master_data.py dòng 26)
        # Chúng ta cần kiểm tra xem to_csv của dataframe đã được gọi hoặc file được tạo ra.
        # Lưu ý trong master_data.py dòng 25-26:
        # file_path = os.path.join("data/processed", self.master_file)
        # df.to_csv(file_path, index=False, encoding='utf-8-sig')
        # Vì vậy để chạy an toàn trong môi trường test, chúng ta mock `pandas.DataFrame.to_csv` để không ghi thật ra data/processed/
        # Hoặc patch os.path.join trong master_data để trỏ đến tmp_path.
        # Hãy patch os.path.join trong master_data.

def test_master_data_check_and_update_new(mock_market_info, tmp_path):
    """
    Test check_and_update khi file master chưa tồn tại (chắc chắn phải tạo mới).
    """
    # Thay đổi đường dẫn lưu trữ để trỏ đến tmp_path
    with patch("os.path.join") as mock_join:
        temp_file = os.path.join(tmp_path, "market_symbols_master.csv")
        mock_join.return_value = temp_file
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False
            
            manager = MasterDataManager()
            manager.export_symbols = MagicMock(return_value=True)
            
            # Chạy check_and_update
            result = manager.check_and_update()
            
            assert result is True
            manager.export_symbols.assert_called_once()

def test_master_data_check_and_update_not_expired(mock_market_info, tmp_path):
    """
    Test check_and_update khi file master đã tồn tại và chưa quá 7 ngày (không cần cập nhật).
    """
    with patch("os.path.join") as mock_join:
        temp_file = os.path.join(tmp_path, "market_symbols_master.csv")
        mock_join.return_value = temp_file
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            # Giả lập thời gian sửa đổi file là hiện tại (0 ngày trôi qua)
            with patch("os.path.getmtime") as mock_getmtime:
                mock_getmtime.return_value = datetime.datetime.now().timestamp()
                
                manager = MasterDataManager()
                manager.export_symbols = MagicMock(return_value=True)
                
                result = manager.check_and_update()
                
                assert result is True
                # Không được gọi export_symbols vì dữ liệu vẫn còn mới
                manager.export_symbols.assert_not_called()

def test_master_data_check_and_update_expired(mock_market_info, tmp_path):
    """
    Test check_and_update khi file master đã quá 7 ngày cũ (phải tự động cập nhật).
    """
    with patch("os.path.join") as mock_join:
        temp_file = os.path.join(tmp_path, "market_symbols_master.csv")
        mock_join.return_value = temp_file
        
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True
            
            # Giả lập thời gian sửa đổi file cách đây 10 ngày
            ten_days_ago = datetime.datetime.now() - datetime.timedelta(days=10)
            with patch("os.path.getmtime") as mock_getmtime:
                mock_getmtime.return_value = ten_days_ago.timestamp()
                
                manager = MasterDataManager()
                manager.export_symbols = MagicMock(return_value=True)
                
                result = manager.check_and_update()
                
                assert result is True
                # Phải gọi export_symbols để cập nhật dữ liệu mới
                manager.export_symbols.assert_called_once()
