from src.crawlers.vnstock_crawler import VnstockCrawler
from src.utils.logger import logger
import json
import datetime

def test_vnstock():
    crawler = VnstockCrawler()
    
    symbol = "FPT"
    
    logger.info(f"--- Testing Vnstock3 for {symbol} ---")
    
    # 1. Test Realtime Price (Mô phỏng bằng nến phút gần nhất)
    logger.info("1. Testing Realtime/Recent Price...")
    recent_data = crawler.fetch_realtime_price(symbol)
    if recent_data:
        print("Recent Data (Last 1m candle):")
        print(json.dumps(recent_data, indent=2, ensure_ascii=False, default=str))
    
    # 2. Test Historical Price
    logger.info("2. Testing Historical Price (Last 7 days)...")
    end_date = datetime.date.today().strftime("%Y-%m-%d")
    start_date = (datetime.date.today() - datetime.timedelta(days=7)).strftime("%Y-%m-%d")
    
    history = crawler.fetch_historical_price(symbol, start_date, end_date)
    print(f"Fetched {len(history)} historical records.")
    if history:
        print("First record in range:")
        print(json.dumps(history[0], indent=2, ensure_ascii=False, default=str))

    # 3. Test Financial Info
    logger.info("3. Testing Financial Indicators...")
    finance = crawler.fetch_financial_info(symbol)
    if finance:
        print("Key Financial Ratios (Latest Year):")
        # Chỉ in ra 5 chỉ số đầu tiên để tránh quá dài
        summary = {k: finance[k] for k in list(finance.keys())[:5]}
        print(json.dumps(summary, indent=2, ensure_ascii=False, default=str))

if __name__ == "__main__":
    test_vnstock()
