import sys
import os

# Thêm site-packages của venv vào sys.path
sys.path.insert(0, r"C:\Users\Admin\stock-crawler\venv\Lib\site-packages")
# Thêm thư mục gốc dự án vào sys.path
sys.path.insert(0, r"C:\Users\Admin\stock-crawler")

# Import pytest từ site-packages của venv
import pytest

if __name__ == "__main__":
    print("--- PATH CONFIGURATION COMPLETED ---")
    print(f"System Python: {sys.executable}")
    print(f"Targeting Tests Path: {os.path.abspath('tests/unit')}")
    print("-----------------------------------")
    
    # Chạy pytest thông qua hàm main chính thức với đường dẫn tuyệt đối tới thư mục test
    exit_code = pytest.main([
        r"C:\Users\Admin\stock-crawler\tests\unit",
        r"--rootdir=C:\Users\Admin\stock-crawler",
        "-v",
        "-p", "no:logging",
        "-p", "no:capture"
    ])
    sys.exit(exit_code)

