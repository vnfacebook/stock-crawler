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

    # 2. Crawl Data Hàng Ngày (Thứ 2 đến Thứ 6 lúc 18:00)
    scheduler.add_job(
        job_daily_crawl,
        trigger=CronTrigger(day_of_week='mon-fri', hour=18, minute=0),
        id='daily_market_crawl',
        name='Daily market data crawling',
        replace_existing=True
    )

    # In danh sách các công việc đã lên lịch
    logger.info("Scheduled Jobs:")
    for job in scheduler.get_jobs():
        logger.info(f" - {job.name}: Next run at {job.next_run_time}")

    # Chạy vòng lặp vô hạn
    try:
        logger.info("Scheduler is now running. Press Ctrl+C to exit.")
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler interrupted by user. Shutting down gracefully...")
        scheduler.shutdown()

if __name__ == "__main__":
    main()
