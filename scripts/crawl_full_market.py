from src.crawlers.vnstock_crawler import VnstockCrawler
from src.crawlers.market_info import MarketInfo
from src.storage.csv_writer import CSVWriter
from src.storage.bigquery_writer import BigQueryWriter
from src.utils.logger import logger
from dotenv import load_dotenv
import datetime
import time
import sys
import os

def crawl_full_market(limit=None, start_date=None, end_date=None):
    """
    Crawl dữ liệu cho toàn bộ thị trường với cơ chế tự động chờ khi bị Rate Limit.
    Nếu không truyền start_date, end_date, mặc định lấy dữ liệu 1 năm qua.
    """
    load_dotenv()
    crawler = VnstockCrawler()
    market = MarketInfo()
    csv_writer = CSVWriter()
    bq_writer = BigQueryWriter()
    
    # 1. Lấy danh sách mã
    symbols = market.get_all_symbols()
    
    if not symbols:
        logger.error("No symbols found. Aborting.")
        return

    if limit:
        symbols = symbols[:limit]
        logger.info(f"Limiting crawl to {limit} symbols for testing.")

    # 2. Thiết lập thời gian (Lấy 1 năm nếu không truyền vào)
    if not end_date:
        end_date = datetime.date.today().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.date.today() - datetime.timedelta(days=365)).strftime("%Y-%m-%d")
    
    logger.info(f"Starting crawl for {len(symbols)} symbols. Range: {start_date} to {end_date}")

    # Checkpoint logic
    # Tên file checkpoint đi kèm với khoảng thời gian crawl để không bị lẫn lộn giữa các ngày
    checkpoint_file = f"data/processed/crawled_symbols_{start_date}_to_{end_date}.txt"
    crawled_symbols = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, 'r', encoding='utf-8') as f:
            crawled_symbols = set(line.strip() for line in f if line.strip())
        logger.info(f"Loaded {len(crawled_symbols)} symbols from checkpoint.")

    BATCH_SIZE = 50
    history_batch = []
    finance_batch = []
    checkpoint_batch = []

    index = 0
    while index < len(symbols):
        symbol = symbols[index]
        
        if symbol in crawled_symbols:
            logger.info(f"[{index + 1}/{len(symbols)}] Skipping {symbol} (already crawled).")
            index += 1
            continue

        logger.info(f"[{index + 1}/{len(symbols)}] Processing {symbol}...")
        
        try:
            # Lấy lịch sử giá
            history = crawler.fetch_historical_price(symbol, start_date, end_date)
            if history:
                history_batch.extend(history)
            
            # Lấy thông tin tài chính
            finance = crawler.fetch_financial_info(symbol)
            if finance:
                finance['symbol'] = symbol
                finance['fetched_at'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                finance_batch.append(finance)

            checkpoint_batch.append(symbol)

            # --- BATCH SAVE LOGIC (CSV + BIGQUERY) ---
            if len(checkpoint_batch) >= BATCH_SIZE or index == len(symbols) - 1:
                logger.info(f"Flushing batch of {len(checkpoint_batch)} symbols to Storage...")
                
                # Save to CSV
                if history_batch:
                    csv_writer.save(history_batch, "market_history_full.csv")
                if finance_batch:
                    csv_writer.save(finance_batch, "market_finance_full.csv")
                
                # Save to BigQuery
                if history_batch:
                    bq_writer.save(history_batch, "market_history_full")
                if finance_batch:
                    bq_writer.save(finance_batch, "market_finance_full")

                # Lưu checkpoint thành công
                with open(checkpoint_file, 'a', encoding='utf-8') as f:
                    for s in checkpoint_batch:
                        f.write(f"{s}\n")
                        crawled_symbols.add(s)

                history_batch.clear()
                finance_batch.clear()
                checkpoint_batch.clear()

            # Tiến tới mã tiếp theo
            index += 1
            
            # Delay an toàn để duy trì dưới ngưỡng 20 req/phút cho gói Guest
            # (Mỗi mã thực hiện 2-3 req, nên cần nghỉ khoảng 6-8s)
            time.sleep(6.5)
            
        except (Exception, SystemExit) as e:
            err_msg = str(e)
            if "Rate limit" in err_msg or "429" in err_msg or "20 requests" in err_msg or not err_msg:
                logger.warning(f"Rate limit detected or process interrupted at {symbol}. Waiting 65 seconds to cool down...")
                time.sleep(65)
                # Không tăng index để thử lại mã hiện tại
                continue
            else:
                logger.error(f"Unexpected error for {symbol}: {err_msg}. Skipping to next.")
                index += 1
                time.sleep(2)

    logger.info("Full market crawl completed.")

if __name__ == "__main__":
    # Để crawl toàn bộ, bạn có thể gọi crawl_full_market() không tham số.
    # Ở đây tôi đặt mặc định crawl 1535 mã nhưng bạn có thể dừng bất cứ lúc nào.
    try:
        crawl_full_market()
    except KeyboardInterrupt:
        logger.info("Crawl interrupted by user.")
