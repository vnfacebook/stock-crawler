from scripts.crawl_full_market import crawl_full_market
from src.storage.master_data import MasterDataManager
from src.utils.logger import logger
import datetime
import os

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
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        last_date = get_last_successful_date()
        
        if last_date:
            # Lấy ngày cuối cùng chạy thành công + 1 ngày
            last_date_obj = datetime.datetime.strptime(last_date, "%Y-%m-%d").date()
            start_date_obj = last_date_obj + datetime.timedelta(days=1)
            
            # Nếu ngày bắt đầu > ngày hôm nay thì tức là đã chạy rồi
            if start_date_obj > datetime.date.today():
                logger.info(f"Data is already up to date (last run: {last_date}). Skipping.")
                return
                
            start_date = start_date_obj.strftime("%Y-%m-%d")
        else:
            # Lần đầu tiên chạy tự động, lấy đúng hôm nay
            start_date = today_str

        logger.info(f"Target Date Range: {start_date} to {today_str}")
        
        # Chạy crawl
        crawl_full_market(start_date=start_date, end_date=today_str)
        
        # Lưu lại mốc thời gian thành công
        set_last_successful_date(today_str)
        
        logger.info("--- FINISHED JOB: Daily Crawl ---")
    except Exception as e:
        logger.error(f"--- FAILED JOB: Daily Crawl --- | Error: {str(e)}")
