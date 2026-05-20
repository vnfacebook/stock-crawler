from src.crawlers.market_info import MarketInfo
from src.storage.csv_writer import CSVWriter
from src.utils.logger import logger
import os
import datetime

class MasterDataManager:
    def __init__(self):
        self.market = MarketInfo()
        self.writer = CSVWriter(base_path="data/processed")
        self.master_file = "market_symbols_master.csv"

    def export_symbols(self):
        """
        Xuất toàn bộ danh sách mã chứng khoán và thông tin công ty ra file master data.
        """
        try:
            logger.info("Exporting market master data...")
            df = self.market.get_companies_info()
            if not df.empty:
                # Thêm cột ngày cập nhật
                df['updated_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # Lưu file (ghi đè để luôn mới nhất)
                file_path = os.path.join("data/processed", self.master_file)
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                logger.info(f"Master data exported to {file_path}. Total: {len(df)} symbols.")
                return True
            return False
        except Exception as e:
            logger.error(f"Error exporting master data: {str(e)}")
            return False

    def check_and_update(self, force=False):
        """
        Kiểm tra và cập nhật file master data định kỳ (mặc định 7 ngày/lần).
        """
        file_path = os.path.join("data/processed", self.master_file)
        
        if not os.path.exists(file_path) or force:
            return self.export_symbols()

        # Kiểm tra ngày cập nhật cuối cùng
        file_time = datetime.datetime.fromtimestamp(os.path.getmtime(file_path))
        days_passed = (datetime.datetime.now() - file_time).days
        
        if days_passed >= 7:
            logger.info(f"Master data is {days_passed} days old. Updating...")
            return self.export_symbols()
        else:
            logger.info(f"Master data is up to date (last updated {days_passed} days ago).")
            return True

if __name__ == "__main__":
    # Test export
    manager = MasterDataManager()
    manager.export_symbols()
