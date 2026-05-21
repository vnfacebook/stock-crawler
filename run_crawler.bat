@echo off
cls
title Antigravity Stock Crawler System
color 0B
echo ====================================================================
echo                 ANTIGRAVITY STOCK CRAWLER SYSTEM                    
echo ====================================================================
echo.
echo  [+] KHOI DONG: Dang thiet lap moi truong...
cd /d "C:\Users\Admin\stock-crawler"

if not exist "C:\Users\Admin\stock-crawler\venv\Scripts\activate.bat" goto no_venv

echo  [+] KICH HOAT: Dang kich hoat moi truong venv...
call .\venv\Scripts\activate.bat

echo  [+] BAT DAU: Dang khoi chay Trinh lap lich tu dong...
echo  [+] CHU Y: He thong se kiem tra va crawl bu du lieu NGAY LAP TUC khi khoi dong.
echo  [+] HUONG DAN: De he thong tiep tuc tu dong crawl luc 15:30, vui long 
echo                 khong tat cua so nay. Nhan Ctrl+C de dung.
echo.
echo ====================================================================
echo.

python scripts/run_scheduler.py

echo.
echo ====================================================================
echo  [+] HE THONG DA DUNG HOAT DONG.
echo ====================================================================
pause
exit /b

:no_venv
color 0C
echo.
echo  [Loi] Khong tim thay thu muc moi truong ao venv tai:
echo        C:\Users\Admin\stock-crawler\venv
echo  [Goi y] Vui long kiem tra lai va chay lai file nay.
echo.
pause
exit /b
