import os
import sys

# Thêm thư mục gốc vào đường dẫn hệ thống để dễ import
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from src.scheduler.jobs import job_update_master_data, job_daily_crawl
from src.utils.logger import logger

def main():
    logger.info("Initializing APScheduler (Timezone: Asia/Ho_Chi_Minh)...")
    
    # Sử dụng BlockingScheduler (chặn tiến trình hiện tại để chạy vòng lặp scheduler)
    scheduler = BlockingScheduler(timezone="Asia/Ho_Chi_Minh")

    # 1. Cập nhật Master Data (Sáng sớm thứ 2 hàng tuần lúc 08:00)
    scheduler.add_job(
        job_update_master_data,
        trigger=CronTrigger(day_of_week='mon', hour=8, minute=0),
        id='update_master_data',
        name='Update master symbols dictionary',
        replace_existing=True
    )

    # 2. Crawl Data Hàng Ngày (Thứ 2 đến Thứ 6 lúc 15:30)
    scheduler.add_job(
        job_daily_crawl,
        trigger=CronTrigger(day_of_week='mon-fri', hour=15, minute=30),
        id='daily_market_crawl',
        name='Daily market data crawling',
        replace_existing=True
    )

    # In danh sách các công việc đã lên lịch
    logger.info("Scheduled Jobs:")
    for job in scheduler.get_jobs():
        try:
            next_run = job.next_run_time
        except AttributeError:
            next_run = "Pending startup (Asia/Ho_Chi_Minh)"
        logger.info(f" - {job.name}: Next run at {next_run}")

    # 3. Chạy kiểm tra và crawl bù ngay lập tức khi khởi động trình scheduler (nếu có ngày bị lỡ)
    logger.info("Running initial startup backfill check...")
    try:
        job_daily_crawl()
    except Exception as e:
        logger.error(f"Failed to run initial startup backfill check: {e}")

    # Chạy vòng lặp vô hạn
    try:
        logger.info("Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler interrupted by user. Shutting down gracefully...")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
