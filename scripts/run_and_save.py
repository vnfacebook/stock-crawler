from src.crawlers.vnstock_crawler import VnstockCrawler
from src.storage.csv_writer import CSVWriter
from src.utils.logger import logger
import datetime

def main():
    crawler = VnstockCrawler()
    writer = CSVWriter()
    
    symbols = ["FPT", "VNM"]
    
    for symbol in symbols:
        logger.info(f"--- Processing {symbol} ---")
        
        # 1. Lấy và lưu lịch sử giá
        end_date = datetime.date.today().strftime("%Y-%m-%d")
        start_date = (datetime.date.today() - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
        
        logger.info(f"Fetching 30 days history for {symbol}")
        history = crawler.fetch_historical_price(symbol, start_date, end_date)
        
        if history:
            filename = f"{symbol}_history.csv"
            # Đảm bảo symbol có trong dữ liệu history (mặc dù crawler đã gán, nhưng script cũ có thể ghi đè)
            writer.save(history, filename)
        
        # 2. Lấy và lưu thông tin tài chính
        logger.info(f"Fetching financial info for {symbol}")
        finance = crawler.fetch_financial_info(symbol)
        if finance:
            writer.save(finance, f"{symbol}_finance.csv")
        
        logger.info(f"Finished {symbol}")

if __name__ == "__main__":
    main()
