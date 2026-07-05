@echo off
echo ========================================
echo تحويل برنامج FarmerPro إلى ملف exe
echo ========================================
echo.

REM تثبيت المكتبات المطلوبة
echo [1/3] تثبيت المكتبات المطلوبة...
pip install -r requirements.txt
echo.

REM تحويل البرنامج إلى exe
echo [2/3] تحويل البرنامج إلى ملف تنفيذي...
pyinstaller --onefile --windowed --name "FarmerPro" --icon=icon.ico farmerpro2.pyw
echo.

REM نسخ ملفات إضافية
echo [3/3] نسخ ملفات إضافية...
if exist "lang.json" xcopy "lang.json" "dist\" /Y
if exist "farmerpro.db" xcopy "farmerpro.db" "dist\" /Y
echo.

echo ========================================
echo تم الانتهاء! الملف التنفيذي في مجلد dist
echo ========================================
pause
