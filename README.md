# Stock Crawler Project

Dự án này nhằm mục đích xây dựng một công cụ tự động thu thập (crawl) dữ liệu chứng khoán từ các nguồn phổ biến tại Việt Nam (như SSI, VNDirect, Cafef, Vietstock...).

---

## Mục tiêu
- Thu thập dữ liệu bảng giá thời gian thực.
- Thu thập dữ liệu lịch sử giá (OHLCV).
- Thu thập thông tin tài chính doanh nghiệp (báo cáo tài chính, chỉ số P/E, EPS...).
- Thu thập dữ liệu giao dịch nước ngoài (foreign buy/sell).
- Lưu trữ dữ liệu vào cơ sở dữ liệu hoặc file CSV/JSON.
- Hỗ trợ lên lịch tự động (scheduler) chạy định kỳ trong giờ giao dịch.

---

## Công nghệ đề xuất
- **Ngôn ngữ:** Python 3.10+
- **Thư viện crawl:**
  - `requests`, `httpx` — HTTP client cho trang tĩnh / API
  - `BeautifulSoup4` — parse HTML trang tĩnh
  - `Playwright` — render trang động/SPA (ưu tiên hơn Selenium)
- **Xử lý dữ liệu:** `pandas`, `numpy`
- **Lưu trữ:** `SQLite` (dev) hoặc `PostgreSQL` (production)
- **Scheduler:** `APScheduler` hoặc `cron` (Linux/macOS)
- **Quản lý config:** `python-dotenv`, `pydantic-settings`
- **Logging:** `loguru`
- **Testing:** `pytest`, `pytest-asyncio`
- **AI hỗ trợ phát triển:** Gemini CLI

---

## Quy ước dự án
- Tuân thủ chuẩn **PEP 8** cho code Python.
- Dùng **type hints** cho tất cả function/method.
- Mọi script crawl phải có cơ chế xử lý lỗi và **retry** (exponential backoff).
- Không spam request quá dày — sử dụng **delay ngẫu nhiên** (1–3s) và **proxy rotation** nếu cần.
- Mỗi source crawl là một module độc lập, dễ bật/tắt.
- Dữ liệu raw phải được lưu lại trước khi transform (raw → processed pipeline).
- Commit message theo chuẩn **Conventional Commits** (`feat:`, `fix:`, `chore:`...).

---

## Cấu trúc thư mục (Dự kiến)

```
stock-crawler/
├── src/
│   ├── crawlers/              # Module crawl theo từng nguồn
│   │   ├── base.py            # Abstract base crawler
│   │   ├── ssi.py
│   │   ├── vndirect.py
│   │   ├── cafef.py
│   │   └── vietstock.py
│   ├── parsers/               # Parse & transform dữ liệu thô
│   │   ├── price_parser.py
│   │   └── financial_parser.py
│   ├── storage/               # Tầng lưu trữ
│   │   ├── database.py        # SQLAlchemy models & session
│   │   ├── csv_writer.py
│   │   └── json_writer.py
│   ├── scheduler/             # Lên lịch chạy tự động
│   │   └── jobs.py
│   ├── utils/
│   │   ├── http_client.py     # Wrapper requests với retry/proxy
│   │   ├── logger.py
│   │   └── helpers.py
│   └── config.py              # Cấu hình toàn cục (env vars)
├── data/
│   ├── raw/                   # Dữ liệu thô chưa xử lý
│   └── processed/             # Dữ liệu đã chuẩn hóa
├── tests/
│   ├── unit/
│   └── integration/
├── scripts/
│   └── run_crawler.py         # Entry point thủ công
├── .env.example               # Mẫu biến môi trường
├── .gitignore
├── requirements.txt
├── requirements-dev.txt       # Thư viện chỉ dùng khi dev/test
└── README.md
```

---

## Thiết kế Base Crawler

Mỗi crawler kế thừa từ `BaseCrawler` để đảm bảo interface đồng nhất:

```python
# src/crawlers/base.py
from abc import ABC, abstractmethod
from typing import Any
import time, random
from src.utils.logger import logger

class BaseCrawler(ABC):
    SOURCE_NAME: str = ""
    BASE_URL: str = ""

    def __init__(self, delay: tuple[float, float] = (1.0, 3.0)):
        self.delay = delay

    def _sleep(self):
        time.sleep(random.uniform(*self.delay))

    @abstractmethod
    def fetch_realtime_price(self, symbol: str) -> dict[str, Any]: ...

    @abstractmethod
    def fetch_historical_price(self, symbol: str, from_date: str, to_date: str) -> list[dict]: ...

    @abstractmethod
    def fetch_financial_info(self, symbol: str) -> dict[str, Any]: ...
```

---

## Cơ chế Retry & Anti-block

```python
# src/utils/http_client.py
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def safe_get(url: str, headers: dict = None, proxies: dict = None) -> httpx.Response:
    response = httpx.get(url, headers=headers, proxies=proxies, timeout=15)
    response.raise_for_status()
    return response
```

---

## Nguồn dữ liệu & Phương thức

| Nguồn      | Loại dữ liệu               | Phương thức       | Ghi chú                        |
|------------|----------------------------|-------------------|--------------------------------|
| SSI        | Bảng giá real-time         | WebSocket / REST  | Cần token xác thực             |
| VNDirect   | Lịch sử giá, tài chính     | REST API          | Rate limit ~100 req/min        |
| Cafef      | Tin tức, chỉ số            | HTML scraping     | Trang tĩnh, dễ crawl           |
| Vietstock  | Báo cáo tài chính          | Playwright (SPA)  | Cần render JS                  |
| HOSE/HNX   | Danh sách mã CK            | REST API công khai| Không cần auth                 |

---

## Biến môi trường (.env.example)

```env
# Database
DATABASE_URL=sqlite:///data/stock.db

# Proxy (tuỳ chọn)
PROXY_URL=

# SSI Auth
SSI_API_KEY=
SSI_SECRET_KEY=

# Scheduler
CRAWL_INTERVAL_MINUTES=5
CRAWL_START_TIME=09:00
CRAWL_END_TIME=15:00

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/crawler.log
```

---

## Lộ trình phát triển (Roadmap)

## Lộ trình phát triển (Roadmap)

### Phase 1 — MVP (Đã hoàn thành 100% và kiểm chứng)
- [x] Khởi tạo cấu trúc thư mục và Logging system.
- [x] Triển khai `BaseCrawler` và `HttpClient` với cơ chế Retry.
- [x] Triển khai `VnstockCrawler` sử dụng thư viện `vnstock` (Unified API v4).
- [x] **Master Data:** Triển khai `MasterDataManager` quản lý danh sách 1.535 mã chứng khoán (tự động cập nhật mỗi 7 ngày).
- [x] **Full Market Crawl:** Triển khai script thu thập dữ liệu toàn bộ thị trường với cơ chế **Auto-wait (65s)** khi gặp Rate Limit.
- [x] **Storage:** Hoàn thiện module `CSVWriter` và chuẩn hóa Schema tài chính (**Method B**).
- [x] **Mapping:** Đảm bảo trường `symbol` có mặt trong tất cả các file để liên kết dữ liệu (Master, History, Finance).

---

## Nhật ký lỗi và Giải pháp (Knowledge Base)

### 4. Lệch cột dữ liệu tài chính
- **Vấn đề:** Mỗi công ty có số lượng năm báo cáo khác nhau, dẫn đến file CSV bị lệch cột khi lưu dạng thô.
- **Giải pháp:** Triển khai **Method B (Normalization)**. Chỉ trích xuất các chỉ số quan trọng (P/E, EPS, ROE, ROA...) của năm gần nhất và đưa vào một schema cố định trước khi lưu. Điều này đảm bảo file CSV luôn đồng nhất 100% cột.

### 5. Lỗi lưu pandas Series thay vì giá trị số
- **Vấn đề:** Khi crawler gặp dữ liệu có nhiều cột trùng tên năm (ví dụ nhiều cột '2023'), `row.get(year)` trả về một Series thay vì giá trị đơn lẻ, làm hỏng định dạng CSV.
- **Giải pháp:** Bổ sung logic kiểm tra `isinstance(val, pd.Series)` trong `vnstock_crawler.py`. Nếu là Series, chỉ lấy giá trị đầu tiên (`.iloc[0]`) và ép kiểu về `float`.

### 6. Lỗi lệch cột CSV khi Append (Rất nguy hiểm)
- **Vấn đề:** Khi `pandas` append (`to_csv(mode='a')`) một dict có thứ tự key khác hoặc thiếu key so với file CSV gốc, dữ liệu sẽ bị đẩy sai cột hoàn toàn.
- **Giải pháp:** Trong `CSVWriter`, luôn phải đọc dòng header của file hiện tại (`existing_df = pd.read_csv(file_path, nrows=0)`) và căn chỉnh lại cột bằng `df = df.reindex(columns=existing_columns)` trước khi append.

### 7. Lỗi Checkpoint bỏ sót dữ liệu khi chạy Daily
- **Vấn đề:** File Checkpoint tĩnh (`crawled_symbols.txt`) khiến cho mã cổ phiếu đã chạy thành công hôm qua sẽ bị bỏ qua (Skip) vào ngày hôm nay.
- **Giải pháp:** Đặt tên file checkpoint động theo ngày đang lấy dữ liệu (`crawled_symbols_{start_date}_to_{end_date}.txt`). Mỗi khoảng thời gian sẽ có một file checkpoint độc lập.

### 8. Lỗi thủng dữ liệu khi mất mạng hoặc không chạy
- **Vấn đề:** Lịch chạy tự động luôn gắn cứng `start_date = hôm nay`. Nếu hôm qua máy chủ mất điện, hệ thống sẽ bỏ qua ngày hôm qua vĩnh viễn.
- **Giải pháp:** Thêm cơ chế **Auto-healing (Backfill)**. Lưu lại ngày chạy thành công cuối cùng vào `last_crawl_date.txt`. Khi chạy lại, tự động tính toán `start_date = last_date + 1 ngày` để kéo bù toàn bộ dữ liệu bị lọt lưới.

### 9. Quá tải I/O Ổ cứng (Ghi lẻ tẻ) và BigQuery API Quota
- **Vấn đề:** Vòng lặp 1.535 mã liên tục mở/đóng file CSV và gọi API để gửi từng dòng lên BigQuery gây rớt hiệu năng trầm trọng.
- **Giải pháp:** Implement **Batching Logic**. Tạo các mảng tạm (`history_batch`, `finance_batch`). Gom đủ 50 mã rồi mới gọi hàm `writer.save()` để xả dữ liệu 1 lần.

### 10. Xung đột môi trường Python 3.14 toàn cục (Global Environment)
- **Vấn đề:** Khi chạy bằng lệnh `python` mặc định của hệ thống, hệ thống sử dụng Python 3.14 (bản thử nghiệm toàn cục) gây lỗi xung đột C-API của Numpy (`OverflowError` khi khởi tạo `float128`) và thiếu hụt các thư viện Google Cloud BigQuery.
- **Giải pháp:** Luôn sử dụng môi trường ảo ổn định đã tạo sẵn tại thư mục `venv` dùng phiên bản **Python 3.11.9**. Chỉ chạy các tập lệnh thông qua đường dẫn môi trường ảo: `.\venv\Scripts\python.exe`.

### 11. Lỗi JSON Serialization khi tải dữ liệu Pandas/Numpy lên BigQuery
- **Vấn đề:** Lỗi `Object of type Timestamp is not JSON serializable` hoặc lỗi không thể tuần tự hóa đối tượng Numpy (như `float64`, `int64`, `NaN`, `NaT`) khi gửi dữ liệu thông qua `load_table_from_json` trong thư viện BigQuery Client.
- **Giải pháp:** Bổ sung phương thức `_sanitize_data` đệ quy trong `BigQueryWriter` để làm sạch và chuyển hóa toàn bộ kiểu dữ liệu đặc thù của Pandas/Numpy về kiểu dữ liệu cơ bản của Python (như chuyển `Timestamp`/`datetime` thành chuỗi, `NaN`/`NaT` thành `None`, số thực/nguyên Numpy về standard python float/int).

### 12. Lỗi cấu trúc bảng không khớp BigQuery (`400 Provided Schema does not match`)
- **Vấn đề:** Khi cấu trúc bảng trên BigQuery đã được tạo trước bằng một schema hạn chế (ví dụ dữ liệu test chỉ có 5 cột), việc đẩy dữ liệu chính thức có nhiều cột hơn (như cột `roa`, `roe`, `pb`...) sẽ bị BigQuery từ chối.
- **Giải pháp:** Cấu hình `LoadJobConfig` trong `BigQueryWriter` sử dụng tùy chọn `schema_update_options=[bigquery.SchemaUpdateOption.ALLOW_FIELD_ADDITION]` để BigQuery tự động phát hiện và bổ sung cột mới một cách linh hoạt khi schema thay đổi.

---

## Hướng dẫn tiếp tục dự án
1. **Môi trường hoạt động:** Sử dụng môi trường ảo Python 3.11.9 tại dự án. 
   * **LƯU Ý QUAN TRỌNG:** Tránh chạy lệnh `python` mặc định của hệ thống vì nó đang trỏ đến bản thử nghiệm lỗi Python 3.14. Luôn gọi trực tiếp qua môi trường ảo: `.\venv\Scripts\python.exe`.
2. **Dữ liệu mẫu:** Các file mẫu (FPT, VNM) đã được crawl chuẩn tại `data/processed/`.
3. **Chạy test dọn dẹp các bảng BigQuery cũ (nếu muốn làm sạch schema):**
   ```powershell
   .\venv\Scripts\python.exe scripts/clear_tables.py
   ```
4. **Chạy test crawl dữ liệu thực tế và tải lên BigQuery (Mẫu 3 mã):**
   ```powershell
   .\venv\Scripts\python.exe scripts/test_real_bq.py
   ```
5. **Kích hoạt trình lập lịch scheduler chạy định kỳ:**
   ```powershell
   .\venv\Scripts\python.exe scripts/run_scheduler.py
   ```



### Phase 2 — Mở rộng
- [ ] Thêm các nguồn dữ liệu chuyên sâu (SSI API chính thức, Vietstock).
- [x] Triển khai `DatabaseStorage`: Lưu trữ vào **Google BigQuery** (Đã hoàn thành module `BigQueryWriter`).
- [x] Chuẩn hóa schema dữ liệu (Data Modeling cho MySQL/BigQuery) - Tích hợp cơ chế tự động Batching 50 mã/lần.
- [ ] Viết unit tests cho các module storage.

### Phase 3 — Production
- [x] **Automation:** Đã triển khai `APScheduler` với kịch bản chạy lúc 18:00 (Thứ 2 - Thứ 6) và tự động kéo bù (Backfill) ngày mất dữ liệu.
- [ ] **Deployment:** Đóng gói ứng dụng bằng **Docker** để chạy ổn định trên Server/Cloud.
- [ ] **Monitoring:** Dashboard đơn giản và Alerting qua Telegram khi crawl thất bại.


---

## Lưu ý pháp lý & Đạo đức
- Chỉ crawl dữ liệu **được phép công khai**, không vi phạm Terms of Service.
- Không bán hoặc phân phối dữ liệu crawl được nếu nguồn có bản quyền.
- Đặt `User-Agent` rõ ràng và `delay` đủ để không ảnh hưởng server nguồn.
- Ưu tiên dùng **API chính thức** nếu nguồn có cung cấp.