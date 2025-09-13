import os
import sys
import socket
import subprocess
from pathlib import Path


def get_local_ip():
    """پیدا کردن IP محلی کامپیوتر"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return '192.168.1.1'


def main():
    print("🚀 Zima Mobile Test Server")
    print("=" * 60)

    # پیدا کردن IP محلی
    LOCAL_IP = get_local_ip()
    PORT = 8000

    print(f"📍 IP محلی کامپیوتر: {LOCAL_IP}")
    print(f"🔌 پورت: {PORT}")

    # چک کردن فایل manage.py
    if not Path('manage.py').exists():
        print("❌ فایل manage.py پیدا نشد!")
        print("این اسکریپت را از root پروژه اجرا کنید.")
        return

    # چک کردن فایل .env.local
    if not Path('.env.local').exists():
        print("⚠️  فایل .env.local پیدا نشد!")
        print("لطفاً ابتدا فایل .env.local را ایجاد کنید.")

    print("\n📦 جمع‌آوری Static Files...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'collectstatic', '--noinput'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Static files جمع‌آوری شدند")
        else:
            print("⚠️  مشکل در collectstatic (ادامه می‌دهیم)")
    except Exception as e:
        print(f"⚠️  خطا در collectstatic: {e}")

    print(f"\n🌐 سرور در آدرس‌های زیر در دسترس خواهد بود:")
    print(f"   💻 دسکتاپ: http://127.0.0.1:{PORT}")
    print(f"   📱 موبایل:  http://{LOCAL_IP}:{PORT}")

    print(f"\n📱 مراحل اتصال از موبایل:")
    print(f"   1. موبایل را به همان WiFi وصل کنید")
    print(f"   2. در مرورگر موبایل آدرس زیر را باز کنید:")
    print(f"      http://{LOCAL_IP}:{PORT}")
    print(f"   3. بخش خانوادگی را تست کنید")
    print(f"   4. رفتار hover/touch را بررسی کنید")

    print(f"\n🔄 شروع سرور Django...")
    print("برای توقف سرور Ctrl+C را فشار دهید")
    print("=" * 60)

    # اجرای سرور Django
    try:
        subprocess.run([
            sys.executable, 'manage.py', 'runserver', f'0.0.0.0:{PORT}'
        ])
    except KeyboardInterrupt:
        print("\n\n👋 سرور با موفقیت متوقف شد!")
    except Exception as e:
        print(f"\n❌ خطا در اجرای سرور: {e}")


if __name__ == '__main__':
    main()

#ifconfig | grep "inet " | grep -v 127.0.0.1