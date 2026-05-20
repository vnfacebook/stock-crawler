import pandas as pd
import os
from datetime import datetime
from src.utils.logger import logger

class CSVWriter:
    def __init__(self, base_path: str = "data/processed"):
        self.base_path = base_path
        os.makedirs(base_path, exist_ok=True)

    def save(self, data: list | dict, filename: str):
        """
        Lưu danh sách dict hoặc một dict đơn lẻ vào file CSV.
        """
        if not data:
            logger.warning(f"No data to save for {filename}")
            return

        # Chuyển đổi sang DataFrame
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        else:
            df = pd.DataFrame(data)

        # Tạo đường dẫn file đầy đủ
        file_path = os.path.join(self.base_path, filename)
        
        # Kiểm tra nếu file đã tồn tại để append hoặc ghi mới
        if os.path.exists(file_path):
            try:
                # Đọc headers hiện tại của file
                existing_df = pd.read_csv(file_path, nrows=0)
                existing_columns = existing_df.columns.tolist()
                
                # Căn chỉnh các cột cho khớp với file đã tồn tại
                # Cột nào thiếu trong df mới sẽ được điền NaN, cột thừa sẽ bị bỏ
                df = df.reindex(columns=existing_columns)
            except Exception as e:
                logger.error(f"Error reading headers from {file_path}: {e}")

            df.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8-sig')
            logger.info(f"Appended data to {file_path}")
        else:
            df.to_csv(file_path, mode='w', header=True, index=False, encoding='utf-8-sig')
            logger.info(f"Saved new file {file_path}")
