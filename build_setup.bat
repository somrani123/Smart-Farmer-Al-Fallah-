@echo off
echo ========================================
echo إنشاء ملف التثبيت FarmerPro
echo ========================================
echo.

REM التحقق من وجود ملف exe
if not exist "dist\FarmerPro.exe" (
    echo [خطأ] الملف التنفيذي غير موجود!
    echo يرجى تشغيل build_exe.bat أولاً
    pause
    exit /b 1
)

REM التحقق من وجود Inno Setup Compiler
echo [1/2] التحقق من وجود Inno Setup Compiler...
where iscc >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Inno Setup Compiler غير موجود!
    echo يرجى تثبيت Inno Setup من: https://jrsoftware.org/isdl.php
    pause
    exit /b 1
)

REM إنشاء ملف التثبيت
echo [2/2] إنشاء ملف التثبيت...
iscc FarmerPro_Setup.iss
if %errorlevel% neq 0 (
    echo [خطأ] فشل إنشاء ملف التثبيت
    pause
    exit /b 1
)

echo.
echo ========================================
echo تم الانتهاء! ملف التثبيت في مجلد Output
echo ========================================
pause
