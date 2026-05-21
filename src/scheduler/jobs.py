from scripts.crawl_full_market import crawl_full_market
from src.storage.master_data import MasterDataManager
from src.utils.logger import logger
import datetime
import os

def get_current_time():
    """Trả về thời gian hiện tại. Hỗ trợ mock dễ dàng khi làm unit test."""
    return datetime.datetime.now()


def get_last_successful_date():
    tracker_file = "data/processed/last_crawl_date.txt"
    if os.path.exists(tracker_file):
        with open(tracker_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def set_last_successful_date(date_str):
    tracker_file = "data/processed/last_crawl_date.txt"
    with open(tracker_file, 'w', encoding='utf-8') as f:
        f.write(date_str)

def job_update_master_data():
    """
    Tiến trình tự động cập nhật danh sách mã cổ phiếu (Master Data).
    Khuyến nghị chạy 1 lần/tuần.
    """
    logger.info("--- STARTING JOB: Update Master Data ---")
    try:
        manager = MasterDataManager()
        manager.export_symbols()
        logger.info("--- FINISHED JOB: Update Master Data ---")
    except Exception as e:
        logger.error(f"--- FAILED JOB: Update Master Data --- | Error: {str(e)}")

def job_daily_crawl():
    """
    Tiến trình tự động crawl dữ liệu thị trường (Lịch sử giá, Tài chính).
    Chạy vào ngày làm việc (Thứ 2 - Thứ 6) sau giờ giao dịch.
    Tự động kéo bù (backfill) dữ liệu nếu có ngày bị lỡ (dựa trên last_crawl_date.txt).
    """
    logger.info("--- STARTING JOB: Daily Crawl ---")
    try:
        now = get_current_time()
        market_close_time = datetime.time(15, 30)
        
        # Xác định ngày tối đa có thể crawl (nếu trước 15:30 thì chỉ crawl đến ngày hôm trước)
        if now.time() >= market_close_time:
            max_crawlable_date = now.date()
        else:
            max_crawlable_date = now.date() - datetime.timedelta(days=1)
            
        target_end_date_str = max_crawlable_date.strftime("%Y-%m-%d")
        last_date = get_last_successful_date()
        
        if last_date:
            # Lấy ngày cuối cùng chạy thành công + 1 ngày
            last_date_obj = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
            start_date_obj = last_date_obj + datetime.timedelta(days=1)
            
            # Nếu ngày bắt đầu vượt quá ngày tối đa có thể crawl thì tức là đã cập nhật rồi
            if start_date_obj > max_crawlable_date:
                logger.info(f"Data is already up to date (last run: {last_date}, max crawlable: {target_end_date_str}). Skipping.")
                return
                
            start_date = start_date_obj.strftime("%Y-%m-%d")
        else:
            # Lần đầu tiên chạy tự động, lấy ngày tối đa có thể crawl
            start_date = target_end_date_str

        logger.info(f"Target Date Range: {start_date} to {target_end_date_str}")
        
        # Chạy crawl
        crawl_full_market(start_date=start_date, end_date=target_end_date_str)
        
        # Lưu lại mốc thời gian thành công
        set_last_successful_date(target_end_date_str)
        
        logger.info("--- FINISHED JOB: Daily Crawl ---")
    except Exception as e:
        logger.error(f"--- FAILED JOB: Daily Crawl --- | Error: {str(e)}")
