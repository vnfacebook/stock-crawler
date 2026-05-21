import pytest
from unittest.mock import patch, MagicMock
import datetime
from src.scheduler.jobs import job_daily_crawl

@patch("src.scheduler.jobs.get_last_successful_date")
@patch("src.scheduler.jobs.set_last_successful_date")
@patch("src.scheduler.jobs.crawl_full_market")
@patch("src.scheduler.jobs.logger")
@patch("src.scheduler.jobs.get_current_time")
def test_job_daily_crawl_after_hours_already_updated(mock_get_time, mock_logger, mock_crawl, mock_set_date, mock_get_date):
    """
    Test: Chạy lúc 16:00 (sau 15:30), dữ liệu đã cập nhật đến hôm nay.
    Kết quả: Bỏ qua không crawl.
    """
    mock_now = datetime.datetime(2026, 5, 21, 16, 0, 0)
    mock_get_time.return_value = mock_now
    mock_get_date.return_value = "2026-05-21"
    
    job_daily_crawl()
    
    mock_crawl.assert_not_called()
    mock_logger.info.assert_any_call("Data is already up to date (last run: 2026-05-21, max crawlable: 2026-05-21). Skipping.")

@patch("src.scheduler.jobs.get_last_successful_date")
@patch("src.scheduler.jobs.set_last_successful_date")
@patch("src.scheduler.jobs.crawl_full_market")
@patch("src.scheduler.jobs.logger")
@patch("src.scheduler.jobs.get_current_time")
def test_job_daily_crawl_before_hours_already_updated(mock_get_time, mock_logger, mock_crawl, mock_set_date, mock_get_date):
    """
    Test: Chạy lúc 08:00 sáng (trước 15:30), dữ liệu hôm qua đã được cập nhật đầy đủ.
    Kết quả: Bỏ qua không crawl.
    """
    mock_now = datetime.datetime(2026, 5, 22, 8, 0, 0)
    mock_get_time.return_value = mock_now
    mock_get_date.return_value = "2026-05-21"
    
    job_daily_crawl()
    
    mock_crawl.assert_not_called()
    mock_logger.info.assert_any_call("Data is already up to date (last run: 2026-05-21, max crawlable: 2026-05-21). Skipping.")

@patch("src.scheduler.jobs.get_last_successful_date")
@patch("src.scheduler.jobs.set_last_successful_date")
@patch("src.scheduler.jobs.crawl_full_market")
@patch("src.scheduler.jobs.logger")
@patch("src.scheduler.jobs.get_current_time")
def test_job_daily_crawl_before_hours_needs_backfill(mock_get_time, mock_logger, mock_crawl, mock_set_date, mock_get_date):
    """
    Test: Chạy lúc 08:00 sáng (trước 15:30), nhưng ngày hôm qua (2026-05-21) chưa crawl.
    Lần chạy gần nhất là 2026-05-20.
    Kết quả: Kéo bù dữ liệu cho ngày 2026-05-21.
    """
    mock_now = datetime.datetime(2026, 5, 22, 8, 0, 0)
    mock_get_time.return_value = mock_now
    mock_get_date.return_value = "2026-05-20"
    
    job_daily_crawl()
    
    # Phải crawl từ ngày 2026-05-21 đến ngày 2026-05-21
    mock_crawl.assert_called_once_with(start_date="2026-05-21", end_date="2026-05-21")
    mock_set_date.assert_called_once_with("2026-05-21")
    mock_logger.info.assert_any_call("Target Date Range: 2026-05-21 to 2026-05-21")

@patch("src.scheduler.jobs.get_last_successful_date")
@patch("src.scheduler.jobs.set_last_successful_date")
@patch("src.scheduler.jobs.crawl_full_market")
@patch("src.scheduler.jobs.logger")
@patch("src.scheduler.jobs.get_current_time")
def test_job_daily_crawl_after_hours_needs_crawl(mock_get_time, mock_logger, mock_crawl, mock_set_date, mock_get_date):
    """
    Test: Chạy lúc 16:00 chiều (sau 15:30), cần crawl dữ liệu ngày hôm nay.
    Lần chạy gần nhất là ngày hôm qua 2026-05-20.
    Kết quả: Crawl ngày hôm nay 2026-05-21.
    """
    mock_now = datetime.datetime(2026, 5, 21, 16, 0, 0)
    mock_get_time.return_value = mock_now
    mock_get_date.return_value = "2026-05-20"
    
    job_daily_crawl()
    
    mock_crawl.assert_called_once_with(start_date="2026-05-21", end_date="2026-05-21")
    mock_set_date.assert_called_once_with("2026-05-21")
    mock_logger.info.assert_any_call("Target Date Range: 2026-05-21 to 2026-05-21")
