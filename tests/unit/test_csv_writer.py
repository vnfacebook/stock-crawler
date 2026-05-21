import os
import pandas as pd
import pytest
from src.storage.csv_writer import CSVWriter

def test_csv_writer_save_new(tmp_path):
    """
    Test ghi mới file CSV từ một dict hoặc danh sách dict.
    """
    writer = CSVWriter(base_path=str(tmp_path))
    data = {"symbol": "FPT", "price": 95.5, "volume": 100000}
    filename = "test_new.csv"
    
    writer.save(data, filename)
    
    file_path = os.path.join(tmp_path, filename)
    assert os.path.exists(file_path)
    
    df = pd.read_csv(file_path)
    assert len(df) == 1
    assert df.loc[0, "symbol"] == "FPT"
    assert df.loc[0, "price"] == 95.5
    assert df.loc[0, "volume"] == 100000

def test_csv_writer_save_append_aligned(tmp_path):
    """
    Test append dữ liệu khi các cột căn khớp hoàn toàn.
    """
    writer = CSVWriter(base_path=str(tmp_path))
    filename = "test_append.csv"
    
    # Lần 1: Ghi mới
    data1 = {"symbol": "FPT", "price": 95.5, "volume": 100000}
    writer.save(data1, filename)
    
    # Lần 2: Ghi thêm
    data2 = {"symbol": "VNM", "price": 68.2, "volume": 200000}
    writer.save(data2, filename)
    
    file_path = os.path.join(tmp_path, filename)
    df = pd.read_csv(file_path)
    assert len(df) == 2
    assert df.loc[0, "symbol"] == "FPT"
    assert df.loc[1, "symbol"] == "VNM"
    assert df.loc[1, "price"] == 68.2

def test_csv_writer_save_append_misaligned(tmp_path):
    """
    Test append dữ liệu có cột bị thiếu hoặc thứ tự cột thay đổi (reindex).
    Đảm bảo reindex hoạt động chính xác và không bị lệch cột.
    """
    writer = CSVWriter(base_path=str(tmp_path))
    filename = "test_reindex.csv"
    
    # Lần 1: Ghi cột symbol, price, volume
    data1 = {"symbol": "FPT", "price": 95.5, "volume": 100000}
    writer.save(data1, filename)
    
    # Lần 2: Dict truyền vào bị xáo trộn thứ tự cột và thiếu cột 'volume', thừa cột 'extra'
    # Lưu ý: Cột thừa 'extra' sẽ bị loại bỏ, cột thiếu 'volume' sẽ nhận giá trị NaN
    data2 = {"price": 68.2, "extra": "ignored", "symbol": "VNM"}
    writer.save(data2, filename)
    
    file_path = os.path.join(tmp_path, filename)
    df = pd.read_csv(file_path)
    
    # Cột trong file phải giữ nguyên cấu trúc của lần ghi đầu tiên (symbol, price, volume)
    assert list(df.columns) == ["symbol", "price", "volume"]
    assert len(df) == 2
    
    # Kiểm tra giá trị dòng 2
    assert df.loc[1, "symbol"] == "VNM"
    assert df.loc[1, "price"] == 68.2
    assert pd.isna(df.loc[1, "volume"])
