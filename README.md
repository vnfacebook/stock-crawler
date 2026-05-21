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
- **Phát sinh yêu cầu mới:** Trong quá trình vận hành và phát triển, việc phát sinh các yêu cầu nghiệp vụ mới là hoàn toàn bình thường và được khuyến khích để tối ưu hóa hệ thống. Tuy nhiên, mọi yêu cầu mới cùng giải pháp kỹ thuật tương ứng phải được cập nhật đầy đủ và kịp thời vào file `README.md` này để đảm bảo tính minh bạch và tính kế thừa của dự án.
- **Cập nhật tài liệu:** Mỗi khi thay đổi cấu trúc thư mục, thêm mới, hoặc loại bỏ các file mã nguồn khỏi dự án, nhà phát triển bắt buộc phải cập nhật tương ứng mục **"Bản đồ chỉnh sửa dự án (Developer Modification Guide)"** ở cuối file README này để bản đồ luôn phản ánh chính xác cấu trúc thực tế.

---

## Cấu trúc thư mục (Thực tế)

```
stock-crawler/
├── src/
│   ├── crawlers/              # Module crawl theo từng nguồn
│   │   ├── base.py            # Abstract base crawler
│   │   ├── ssi.py             # SSI Crawler (OAuth2 & iBoard Fallback)
│   │   ├── vndirect.py        # VNDirect Crawler
│   │   ├── cafef.py           # Cafef Static Crawler
│   │   ├── vietstock.py       # Vietstock/TCBS Crawler (Financial Data - Method B)
│   │   └── market_info.py     # Master data symbols generator
│   ├── storage/               # Tầng lưu trữ
│   │   ├── csv_writer.py      # Ghi CSV căn chỉnh khớp cột (Reindex)
│   │   ├── bigquery_writer.py # Nạp BigQuery với clean data đệ quy
│   │   └── master_data.py     # Quản lý master symbols & chu kỳ 7 ngày
│   ├── scheduler/             # Lên lịch chạy tự động
│   │   └── jobs.py            # APScheduler jobs & Auto-Backfill logic
│   ├── utils/
│   │   ├── http_client.py     # Wrapper HTTP client với Tenacity retry
│   │   └── logger.py          # Loguru logger setup
├── data/
│   ├── raw/                   # Dữ liệu thô (raw JSON/CSV)
│   └── processed/             # Dữ liệu chuẩn hóa (processed CSV)
├── tests/
│   └── unit/                  # Bộ Unit Tests toàn diện
│       ├── test_csv_writer.py
│       ├── test_bigquery_writer.py
│       └── test_master_data.py
├── scripts/                   # Tập lệnh vận hành thủ công & kiểm thử
│   ├── run_crawler.py
│   ├── run_scheduler.py       # Điểm khởi chạy trình Scheduler
│   ├── test_real_bq.py        # Chạy kiểm thử tải dữ liệu lên BigQuery thực tế
│   └── clear_tables.py        # Script dọn dẹp bảng BigQuery
├── requirements.txt           # Thư viện chính (APScheduler, vnstock...)
├── requirements-dev.txt       # Thư viện dev/test (pytest, black, flake8...)
├── run_tests.py               # Runner pytest tối ưu phân quyền Sandbox
├── run_crawler.bat            # Tệp lệnh khởi chạy Stock Crawler Pro bằng một click (GOTO-based)
├── stock_crawler.ico          # Biểu tượng ứng dụng Stock Crawler Pro chất lượng cao
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

### 13. Lỗi treo thu thập kiểm thử (Pytest hang ở collecting ...) và lỗi phân quyền 'nul' trong Sandbox Windows
- **Vấn đề:** Khi kích hoạt pytest thông qua `run_command` từ API trong môi trường Sandbox Windows bị giới hạn phân quyền:
  1. Thư mục làm việc mặc định bị trỏ nhầm về thư mục hệ thống `C:\WINDOWS\System32\WindowsPowerShell\v1.0`. Do đó, pytest tự động chọn đây làm `rootdir` và cố gắng quét đệ quy vô hạn hàng nghìn file hệ thống Windows để tìm file test, gây treo tiến trình vĩnh viễn và ngốn sạch CPU.
  2. Pytest mặc định sử dụng thiết bị `nul` để ghi nhận output và log, bị hệ thống sandbox Windows chặn phân quyền (`PermissionError: [Errno 13] Permission denied: 'nul'`).
  3. Môi trường ảo `venv` bị sandbox chặn quyền truy cập dẫn đến lỗi `ModuleNotFoundError: No module named 'pytest'` khi chạy Python hệ thống thường.
- **Giải pháp:**
  1. Sử dụng script điều phối [run_tests.py](file:///C:/Users/Admin/stock-crawler/run_tests.py) và khóa cứng tham số `r"--rootdir=C:\Users\Admin\stock-crawler"` trong `pytest.main()` để pytest không quét bừa bãi ra ngoài dự án.
  2. Vô hiệu hóa triệt để hai plugin logging và capture bằng cách truyền `"-p", "no:logging", "-p", "no:capture"` vào `pytest.main()`.
  3. Luôn kích hoạt chạy kiểm thử thông qua quyền hạn thực tế của người dùng (Bypass Sandbox) hoặc sử dụng đúng python của môi trường ảo cục bộ để thực thi.

### 14. Lỗi giá trị chân lý mơ hồ của DataFrame (ValueError: The truth value of a DataFrame is ambiguous) khi nạp BigQuery
- **Vấn đề:** Trong hàm `save()` của `BigQueryWriter`, logic kiểm tra dữ liệu trống chung `if not data:` sẽ ném ra lỗi ngoại lệ `ValueError` nghiêm trọng nếu tham số `data` truyền vào là một đối tượng `pandas.DataFrame`. Pandas cấm việc đánh giá chân trị trực tiếp trên DataFrame để tránh mơ hồ.
- **Giải pháp:** Bổ sung logic kiểm tra kiểu đối tượng trước:
  ```python
  if isinstance(data, pd.DataFrame):
      if data.empty:
          return
  elif not data:
      return
  ```
  Việc bóc tách kiểm tra `.empty` của DataFrame trước giúp đảm bảo tính an toàn và tương thích hoàn toàn cho cả định dạng Dict đơn lẻ, danh sách Dict, và DataFrame.

### 15. Lỗi Command Prompt bị tắt ngay lập tức (Crash nhấp nháy rồi biến mất) khi chạy file .bat
- **Vấn đề:** Trình thông dịch Windows CMD cực kỳ nhạy cảm với cú pháp đóng mở ngoặc đơn `()` bên trong các khối lệnh `if`. Khi CMD đọc khối `if ( ... )` và gặp chuỗi chứa dấu đóng ngoặc như `(venv)`, nó sẽ hiểu lầm đó là điểm kết thúc của khối lệnh `if`, gây ra lỗi cú pháp và tắt cửa sổ terminal ngay lập tức mà không kịp thông báo lỗi.
- **Giải pháp:** Thiết kế lại file batch khởi chạy [run_crawler.bat](file:///c:/Users/Admin/stock-crawler/run_crawler.bat) bằng kiến trúc phẳng **GOTO** thay vì lồng `if ( ... )`. Sử dụng nhãn `:Label` và lệnh `goto` để điều hướng rẽ nhánh kiểm tra sự tồn tại của môi trường ảo `venv` và file script, giúp script chạy ổn định, tin cậy tuyệt đối và tự động dừng lại (`pause`) để hiển thị thông báo lỗi chi tiết khi có sự cố thay vì biến mất.

### 16. Kéo bù dữ liệu an toàn khi tắt máy giữa chừng (Startup & Recovery Engine)
- **Vấn đề:** Khi chạy trên máy tính cá nhân, người dùng có thể tắt máy trước hoặc trong thời gian thu thập dữ liệu (15:30), hoặc tắt máy khi đang crawl dở dang (ví dụ ở mã thứ 46/50). Lần chạy tiếp theo cần đảm bảo không bỏ sót ngày giao dịch và không bị trùng lặp dữ liệu.
- **Giải pháp:**
  1. **Startup Check:** Khi máy tính khởi động và ứng dụng được mở, scheduler lập tức tính toán ngày giao dịch gần nhất có thể crawl (`max_crawlable_date` dựa trên mốc 15:30 hôm nay). Nếu ngày này lớn hơn ngày lưu trong `last_crawl_date.txt`, scheduler sẽ kích hoạt một tiến trình chạy bù lập tức (Startup Backfill) trước khi chuyển sang trạng thái chờ chạy định kỳ vào 15:30.
  2. **Checkpoint & Batching Safety:** Tiến trình crawl xử lý theo từng lô (Batch 50 mã) và lưu danh sách các mã đã crawl thành công trong ngày vào file checkpoint `crawled_symbols_{date}.txt`. Nếu bị ngắt giữa chừng, lần chạy tiếp theo sẽ tự động đọc checkpoint này và chỉ crawl những mã chưa chạy, đảm bảo **zero data duplication** và bảo toàn tuyệt đối tính toàn vẹn dữ liệu.

---

## Hướng dẫn tiếp tục dự án
1. **Khởi chạy bằng "Stock Crawler Pro" ngoài Desktop (Khuyên dùng cho Máy cá nhân):**
   Để có trải nghiệm chuyên nghiệp giống như một phần mềm độc lập:
   * **Bước 1:** Bấm chuột phải vào file [run_crawler.bat](file:///c:/Users/Admin/stock-crawler/run_crawler.bat) -> Chọn **Show more options** -> **Send to** -> **Desktop (create shortcut)**.
   * **Bước 2:** Ra ngoài màn hình Desktop, nhấp chuột phải vào shortcut vừa tạo -> Chọn **Rename** và đổi tên thành **Stock Crawler Pro**.
   * **Bước 3:** Tiếp tục nhấp chuột phải vào shortcut -> Chọn **Properties** -> Nhấp vào nút **Change Icon...** -> Chọn **Browse...** và trỏ đến file biểu tượng [stock_crawler.ico](file:///c:/Users/Admin/stock-crawler/stock_crawler.ico) nằm trong thư mục gốc dự án. Bấm **OK** rồi **Apply**.
   * **Bắt đầu hoạt động:** Bây giờ, mỗi khi bật máy vào buổi sáng, bạn chỉ cần click đúp vào shortcut **Stock Crawler Pro** ngoài màn hình. Hệ thống sẽ:
     1. Khởi chạy giao diện Terminal xanh lục/đen chuyên nghiệp.
     2. Tự động kiểm tra và thực hiện chạy bù (Startup Backfill) nếu phát hiện ngày giao dịch trước đó chưa được crawl (kể cả khi hôm trước tắt máy đột ngột hoặc mất điện).
     3. Tiếp tục chạy ngầm lập lịch tự động crawl định kỳ vào lúc **15:30** mỗi ngày từ Thứ 2 đến Thứ 6.
2. **Môi trường hoạt động:** Sử dụng môi trường ảo Python 3.11.9 tại dự án. 
   * **LƯU Ý QUAN TRỌNG:** Tránh chạy lệnh `python` mặc định của hệ thống vì nó đang trỏ đến bản thử nghiệm lỗi Python 3.14. Luôn gọi trực tiếp qua môi trường ảo: `.\venv\Scripts\python.exe`.
3. **Dữ liệu mẫu:** Các file mẫu (FPT, VNM) đã được crawl chuẩn tại `data/processed/`.
4. **Chạy test dọn dẹp các bảng BigQuery cũ (nếu muốn làm sạch schema):**
   ```powershell
   .\venv\Scripts\python.exe scripts/clear_tables.py
   ```
5. **Chạy test crawl dữ liệu thực tế và tải lên BigQuery (Mẫu 3 mã):**
   ```powershell
   .\venv\Scripts\python.exe scripts/test_real_bq.py
   ```
6. **Kích hoạt trình lập lịch scheduler chạy định kỳ (Thủ công):**
   ```powershell
   .\venv\Scripts\python.exe scripts/run_scheduler.py
   ```
7. **Kích hoạt chạy bộ Unit Tests tối ưu phân quyền Sandbox:**
   ```powershell
   .\venv\Scripts\python.exe run_tests.py
   ```
   *(Lệnh này sẽ tự động cấu hình đường dẫn và chạy toàn bộ **15/15 bài Unit Tests** toàn diện của dự án chỉ trong ~3.5 giây, đã được tối ưu hóa để bypass lỗi phân quyền Sandbox và ngăn quét đệ quy vô hạn trong các thư mục hệ thống).*

---

## Hướng dẫn vận hành bằng Docker (Docker Deployment Guide)

Dự án đã được cấu hình Docker và Docker Compose đầy đủ, giúp vận hành ứng dụng (trình Scheduler chạy ngầm) cực kỳ ổn định mà không cần lo lắng về cài đặt Python hay môi trường ảo trên server.

### 1. Chuẩn bị trước khi chạy
Đảm bảo bạn đã chuẩn bị đầy đủ các file sau ở thư mục gốc trên host (các file này sẽ được mount tự động vào container):
- File cấu hình [.env](file:///C:/Users/Admin/stock-crawler/.env) (chứa cấu hình BigQuery, Project ID, Dataset ID, v.v.).
- File key tài khoản dịch vụ [credentials.json](file:///C:/Users/Admin/stock-crawler/credentials.json).

### 2. Các lệnh quản lý Docker Compose

* **Khởi dựng và chạy container ở chế độ nền (Detached mode):**
  ```bash
  docker compose up -d --build
  ```
  *(Lệnh này sẽ tự động xây dựng Image dựa trên Python 3.11-slim ổn định, cài đặt dependencies và kích hoạt container)*

* **Xem logs hoạt động của crawler trong container:**
  ```bash
  docker compose logs -f stock-crawler
  ```

* **Dừng hoạt động và gỡ bỏ container:**
  ```bash
  docker compose down
  ```

### 3. Cơ chế bảo toàn dữ liệu (Data Persistence)
Container đã được thiết lập gắn kết các phân vùng ổ đĩa (Volumes) từ container ra ngoài máy host:
- Dữ liệu CSV thu thập được sẽ tự động đồng bộ ra thư mục cục bộ `./data` trên máy host.
- Nhật ký hoạt động chi tiết đồng bộ ra `./logs` trên máy host.

---

### Phase 2 — Mở rộng (Đã hoàn thành 100% và kiểm chứng)
- [x] Thêm các nguồn dữ liệu chuyên sâu: Nâng cấp `SSICrawler` hỗ trợ OAuth2 Fast Connect API chính thức và cơ chế fallback iBoard; triển khai `VietstockCrawler` thu thập báo cáo tài chính qua thư viện `vnstock` v4 (TCBS) với schema chuẩn hóa cố định (Method B).
- [x] Triển khai `DatabaseStorage`: Lưu trữ vào **Google BigQuery** (Đã hoàn thành module `BigQueryWriter`).
- [x] Chuẩn hóa schema dữ liệu (Data Modeling cho MySQL/BigQuery) - Tích hợp cơ chế tự động Batching 50 mã/lần.
- [x] Viết unit tests cho các module storage (`pytest` + `pytest-asyncio` đạt 100% Passed).


### Phase 3 — Production
- [x] **Automation:** Đã triển khai `APScheduler` với kịch bản chạy lúc 15:30 (Thứ 2 - Thứ 6) và tự động kéo bù (Backfill) ngày mất dữ liệu.
- [x] **Deployment:** Đóng gói ứng dụng bằng **Docker** để chạy ổn định trên Server/Cloud.
- [ ] **Monitoring:** Dashboard đơn giản và Alerting qua Telegram khi crawl thất bại.


---

## Bản đồ chỉnh sửa dự án (Developer Modification Guide)

Khi tiếp tục thực hiện hoặc nâng cấp dự án này, bạn có thể tham chiếu nhanh bản đồ dưới đây để biết chính xác cần chỉnh sửa file code nào tương ứng với yêu cầu chỉnh sửa logic hoặc giao diện:

### 1. Muốn chỉnh sửa LOGIC CRAWL DỮ LIỆU?
* **Crawl lịch sử giá & chỉ số tài chính từ vnstock v4 (nguồn chính):** 
  👉 Sửa đổi logic tại [vnstock_crawler.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/vnstock_crawler.py).
* **Crawl dữ liệu từ Cafef (tin tức, chỉ số phụ):** 
  👉 Sửa đổi logic tại [cafef.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/cafef.py).
* **Crawl bảng giá real-time từ SSI (Fast Connect API OAuth2 hoặc fallback iBoard công khai):** 
  👉 Sửa đổi logic tại [ssi.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/ssi.py) hoặc [vndirect.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/vndirect.py).
* **Crawl báo cáo tài chính doanh nghiệp từ Vietstock/TCBS (Method B chuẩn hóa schema):** 
  👉 Sửa đổi logic tại [vietstock.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/vietstock.py).
* **Thay đổi logic lấy danh sách tất cả các mã chứng khoán (HOSE, HNX, UPCOM):** 
  👉 Sửa đổi logic tại [market_info.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/market_info.py).
* **Thay đổi cơ chế delay / sleep an toàn giữa các lượt crawl để tránh bị chặn:** 
  👉 Sửa đổi các tham số mặc định tại [base.py](file:///C:/Users/Admin/stock-crawler/src/crawlers/base.py).

### 2. Muốn chỉnh sửa LOGIC LƯU TRỮ DỮ LIỆU (Storage)?
* **Thay đổi cơ chế lưu trữ, làm sạch kiểu dữ liệu JSON, hoặc sửa đổi cài đặt schema tải lên Google BigQuery:** 
  👉 Sửa đổi logic tại [bigquery_writer.py](file:///C:/Users/Admin/stock-crawler/src/storage/bigquery_writer.py).
* **Thay đổi định dạng, tiêu đề cột hoặc cách ghi đè/nối thêm (Append) file CSV cục bộ:** 
  👉 Sửa đổi logic tại [csv_writer.py](file:///C:/Users/Admin/stock-crawler/src/storage/csv_writer.py).
* **Thay đổi cách quản lý, cập nhật hoặc lọc danh sách mã master (Master Symbols list):** 
  👉 Sửa đổi logic tại [master_data.py](file:///C:/Users/Admin/stock-crawler/src/storage/master_data.py).

### 3. Muốn chỉnh sửa LOGIC LẬP LỊCH TỰ ĐỘNG & ĐIỀU PHỐI (Scheduler)?
* **Thay đổi giờ chạy tự động định kỳ (ví dụ: chuyển từ 18:00 sang giờ khác) hoặc cấu hình các công việc ngầm (APScheduler):** 
  👉 Sửa đổi logic tại [jobs.py](file:///C:/Users/Admin/stock-crawler/src/scheduler/jobs.py).
* **Thay đổi cơ chế Backfill tự động (tự tìm khoảng trống ngày mất điện/mất mạng để chạy bù):** 
  👉 Chỉnh sửa thuật toán tính toán ngày chạy trong [jobs.py](file:///C:/Users/Admin/stock-crawler/src/scheduler/jobs.py).
* **Thay đổi script chạy chính của trình scheduler:** 
  👉 Chỉnh sửa tại [run_scheduler.py](file:///C:/Users/Admin/stock-crawler/scripts/run_scheduler.py).

### 4. Muốn chỉnh sửa QUY TRÌNH CHẠY CHÍNH & BATCHING?
* **Thay đổi kích thước lô gom dữ liệu (Batch Size - ví dụ thay đổi từ 50 mã chứng khoán/lần lưu lên 100 mã):** 
  👉 Chỉnh sửa biến `BATCH_SIZE` trong hàm `crawl_full_market` tại [crawl_full_market.py](file:///C:/Users/Admin/stock-crawler/scripts/crawl_full_market.py).
* **Thay đổi khoảng thời gian crawl mặc định khi chạy thủ công:** 
  👉 Chỉnh sửa hàm `crawl_full_market` tại [crawl_full_market.py](file:///C:/Users/Admin/stock-crawler/scripts/crawl_full_market.py).

### 5. Muốn chỉnh sửa GIAO DIỆN (UI/UX) HOẶC BÁO CÁO (Dashboard)?
* Dự án hiện tại hoạt động dưới dạng **Backend CLI Tool** chạy ngầm tự động đẩy dữ liệu lên BigQuery để làm nguồn cấp cho các BI Tool (như Looker Studio).
* Nếu trong tương lai muốn bổ sung **Dashboard hiển thị hoặc cấu hình trực quan**:
  * Tạo thêm thư mục UI mới tại `src/dashboard/` (khuyến nghị dùng **Streamlit** hoặc **Next.js/Vite**).
  * Tạo các endpoint API để truy vấn dữ liệu từ BigQuery hoặc SQLite tại một file mới trong thư mục `src/api/`.

### 6. Muốn cấu hình HỆ THỐNG & LOGGER?
* **Thay đổi các biến môi trường (Database URL, BigQuery Project ID, Dataset ID, API Keys):** 
  👉 Sửa đổi tại file cấu hình [.env](file:///C:/Users/Admin/stock-crawler/.env) (tham chiếu file mẫu [.env.example](file:///C:/Users/Admin/stock-crawler/.env.example)).
* **Thay đổi định dạng log, cấp độ log (LOG_LEVEL) hoặc nơi lưu trữ log file:** 
  👉 Sửa đổi tại [logger.py](file:///C:/Users/Admin/stock-crawler/src/utils/logger.py).
* **Thay đổi cơ chế gọi HTTP client, cấu hình retry tự động hoặc proxy rotation:** 
  👉 Sửa đổi tại [http_client.py](file:///C:/Users/Admin/stock-crawler/src/utils/http_client.py).

### 7. Muốn chỉnh sửa ĐÓNG GÓI DOCKER & DEPLOYMENT?
* **Thay đổi Image nền, các bước cài đặt hệ thống hoặc môi trường chạy bên trong Container:** 
  👉 Sửa đổi tại [Dockerfile](file:///C:/Users/Admin/stock-crawler/Dockerfile).
* **Thay đổi cấu hình gán ổ đĩa (Volumes), liên kết môi trường, cổng hoặc chính sách Restart:** 
  👉 Sửa đổi tại [docker-compose.yml](file:///C:/Users/Admin/stock-crawler/docker-compose.yml).
* **Thay đổi các tệp/thư mục được bỏ qua không đưa vào tiến trình Docker build:** 
  👉 Sửa đổi tại [.dockerignore](file:///C:/Users/Admin/stock-crawler/.dockerignore).

### 8. Muốn chỉnh sửa hoặc bổ sung UNIT TESTS?
* **Thay đổi bộ kiểm thử cho logic ghi, append, và reindex của CSVWriter:** 
  👉 Sửa đổi tại [test_csv_writer.py](file:///C:/Users/Admin/stock-crawler/tests/unit/test_csv_writer.py).
* **Thay đổi bộ kiểm thử logic làm sạch dữ liệu đệ quy và nạp dữ liệu của BigQueryWriter:** 
  👉 Sửa đổi tại [test_bigquery_writer.py](file:///C:/Users/Admin/stock-crawler/tests/unit/test_bigquery_writer.py).
* **Thay đổi bộ kiểm thử logic kiểm tra và cập nhật Master Symbols tự động:** 
  👉 Sửa đổi tại [test_master_data.py](file:///C:/Users/Admin/stock-crawler/tests/unit/test_master_data.py).
* **Thay đổi script điều phối chạy test trong môi trường giới hạn phân quyền sandbox:** 
  👉 Sửa đổi tại [run_tests.py](file:///C:/Users/Admin/stock-crawler/run_tests.py).

---

## Lưu ý pháp lý & Đạo đức
- Chỉ crawl dữ liệu **được phép công khai**, không vi phạm Terms of Service.
- Không bán hoặc phân phối dữ liệu crawl được nếu nguồn có bản quyền.
- Đặt `User-Agent` rõ ràng và `delay` đủ để không ảnh hưởng server nguồn.
- Ưu tiên dùng **API chính thức** nếu nguồn có cung cấp.