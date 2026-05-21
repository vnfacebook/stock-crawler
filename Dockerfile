# Sử dụng Python 3.11-slim làm base image để đảm bảo dung lượng nhẹ và ổn định nhất
FROM python:3.11-slim

# Thiết lập các biến môi trường cho Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Ho_Chi_Minh

# Thiết lập thư mục làm việc trong container
WORKDIR /app

# Cài đặt tzdata để đồng bộ múi giờ chính xác
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Sao chép và cài đặt các thư viện phụ thuộc
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Sao chép toàn bộ mã nguồn vào container
COPY . .

# Mặc định khởi chạy trình scheduler khi container khởi động
CMD ["python", "scripts/run_scheduler.py"]
