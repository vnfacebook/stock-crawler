from PIL import Image
import os

def main():
    png_path = r"C:\Users\Admin\.gemini\antigravity\brain\61d05495-cf29-47c5-af72-06a4b6d2ff75\stock_crawler_logo_1779347024952.png"
    ico_path = r"C:\Users\Admin\stock-crawler\stock_crawler.ico"
    
    if os.path.exists(png_path):
        print(f"Reading generated PNG from: {png_path}")
        img = Image.open(png_path)
        
        # Lưu dưới dạng file ICO với nhiều kích cỡ tiêu chuẩn của Windows để hiển thị mượt mà nhất
        img.save(
            ico_path, 
            format="ICO", 
            sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        )
        print(f"Successfully generated premium Windows icon at: {ico_path}")
    else:
        print(f"Error: Generated PNG not found at {png_path}")

if __name__ == "__main__":
    main()
