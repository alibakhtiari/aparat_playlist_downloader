# دانلودر ویدیو و لیست پخش آپارات (نسخه ۱.۰.۰)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)](https://github.com/alibakhtiari/aparat_playlist_downloader)

**نرم‌افزار مدرن، سریع و منعطف برای دانلود و استخراج لینک ویدیوها و لیست‌های پخش آپارات به همراه رابط گرافیکی (GUI) و خط فرمان (CLI)**

[English](README.md) | [فارسی](README.fa.md)

</div>

---

## 🌟 قابلیت‌ها و ویژگی‌های کلیدی

- **پشتیبانی سراسری از ورودی‌ها**: امکان پردازش و دانلود هم **لیست‌های پخش (پلی‌لیست)** با شناسه عددی یا آدرس کامل، و هم **تک ویدیوها** با شناسه هش یا لینک صفحه ویدیو.
- **تشخیص همزمان کیفیت‌ها (Multi-threading)**: استعلام موازی و سریع کیفیت‌ها برای تمامی ویدیوهای لیست پخش با استفاده از `ThreadPoolExecutor`.
- **فال‌بک هوشمند کیفیت (Smart Fallback)**: امکان انتخاب کیفیت مورد نظر (`1080p`، `720p`، `480p`، `360p` یا بهترین کیفیت `best`). در صورتی که ویدیویی کیفیت انتخابی را نداشته باشد، بالاترین کیفیت در دسترس به عنوان جایگزین انتخاب می‌شود تا عملیات متوقف نشود.
- **نوارهای پیشرفت زنده و نمایش سرعت**: نمایش نوار وضعیت پیشرفت در ترمینال (با فرمت یونیکد زیبا، درصد، حجم دریافتی و سرعت لحظه‌ای) و در رابط گرافیکی (دو نوار مجزا برای پیشرفت کل صف و پیشرفت فایل جاری).
- **خروجی لینک برای دانلود منیجرها**: امکان استخراج مستقیم لینک‌های CDN آپارات به همراه عنوان ویدیوها در قالب فایل متنی `.txt`، مناسب برای ایمپورت دسته‌ای در دانلود منیجرها مانند Internet Download Manager (IDM)، aria2، curl یا wget.
- **رابط گرافیکی مدرن (GUI) با پشتیبانی راست‌به‌چپ (RTL)**: طراحی شده با PyQt5 بر پایه تم تیره Fusion، دارای جدول مشخصات ویدیوها، انتخاب پوشه خروجی، دکمه توقف عملیات و باز کردن مستقیم پوشه دانلود پس از اتمام.
- **نسخه خط فرمان منعطف (CLI)**: دارای منوی تعاملی و راهنما، به همراه امکان اجرای دستوری با پارامترها و سوییچ‌ها مناسب برای خودکارسازی و اجرا بر روی سرورها و لینوکس بدون رابط گرافیکی.
- **API استاندارد پایتون**: کدنویسی ساختاریافته با تایپ هینت کامل و کلاس `AparatClient` جهت ادغام با پروژه‌های پایتونی دیگر.

---

## 📋 نمونه فرمت‌های ورودی مجاز

| نوع محتوا | فرمت ورودی | نمونه |
| :--- | :--- | :--- |
| **لیست پخش** | شناسه عددی | `11402450` |
| **لیست پخش** | آدرس کامل اینترنتی | `https://www.aparat.com/playlist/11402450` |
| **تک ویدیو** | کد هش ویدیو | `nbl9l8o` |
| **تک ویدیو** | آدرس صفحه ویدیو | `https://www.aparat.com/v/nbl9l8o` |

---

## 📦 پیش‌نیازها و نحوه نصب

### فایل‌های آماده اجرا بدون نیاز به نصب پایتون (Portable Executables)
نسخه‌های باینری و بدون نیاز به نصب برای سیستم‌عامل‌های **ویندوز**، **لینوکس** و **مک** (اپل سیلیکون و اینتل) به صورت خودکار در بخش ریلیزهای گیت‌هاب قرار می‌گیرند:
- به صفحه **[GitHub Releases](https://github.com/alibakhtiari/aparat_playlist_downloader/releases)** مراجعه کنید.
- فایل مناسب با سیستم‌عامل خود را دانلود و مستقیماً اجرا کنید:
  - **ویندوز (x86_64)**: `aparat-dl-windows-amd64.exe` (خط فرمان) و `aparat-gui-windows-amd64.exe` (گرافیکی)
  - **لینوکس (x86_64)**: `aparat-dl-linux-amd64` (خط فرمان) و `aparat-gui-linux-amd64` (گرافیکی)
  - **مک‌اواس (Apple Silicon arm64)**: `aparat-dl-macos-arm64` (خط فرمان) و `aparat-gui-macos-arm64` (گرافیکی)
  - **مک‌اواس (Intel x86_64)**: `aparat-dl-macos-x86_64` (خط فرمان) و `aparat-gui-macos-x86_64` (گرافیکی)

### پیش‌نیازها (اجرا از طریق سورس‌کد پایتون)
- پایتون ۳.۸ یا بالاتر (Python >= 3.8)
- مدیریت پکیج `pip`
- اتصال اینترنت

### ۱. دریافت مخزن
```bash
git clone https://github.com/alibakhtiari/aparat_playlist_downloader.git
cd aparat_playlist_downloader
```

### ۲. نصب وابستگی‌ها

**نصب کامل (رابط گرافیکی + خط فرمان):**
```bash
pip install -r requirements.txt
```
*یا جهت فعال‌سازی دستورات اجرایی مستقیم (`aparat-dl` و `aparat-gui`):*
```bash
pip install -e .
```

**نصب اختصاصی نسخه خط فرمان (مناسب سرورها و لینوکس بدون دسکتاپ):**
```bash
pip install -r cli_requirements.txt
```

---

## 🚀 راهنمای استفاده

### 🖥️ رابط گرافیکی (GUI)

برای اجرای برنامه در محیط گرافیکی:
```bash
python gui.py
# یا در صورت نصب پکیج:
aparat-gui
```

#### مراحل کار با محیط گرافیکی:
1. **ورود آدرس**: لینک یا شناسه لیست پخش یا ویدیو را در کادر ورودی وارد کنید.
2. **دریافت اطلاعات**: روی دکمه **دریافت اطلاعات** کلیک کنید تا نام پلی‌لیست/ویدیو، نام کانال، تعداد و لیست ویدیوها با کیفیت‌های فعال بارگذاری شوند.
3. **تنظیمات**:
   - **کیفیت مورد نظر**: کیفیت دلخواه (بهترین کیفیت، ۱۰۸۰، ۷۲۰ و ...) را انتخاب کنید.
   - **نوع عملیات**: «دانلود ویدیوها» یا «استخراج لینک‌ها (.txt)».
   - **مسیر ذخیره‌سازی**: با کلیک روی «انتخاب پوشه...» مسیر مقصد را مشخص کنید.
4. **اجرا**: روی **شروع عملیات** کلیک کنید. پیشرفت کار و سرعت دانلود لحظه‌ای نمایش داده می‌شود. در هر مرحله امکان لغو عملیات وجود دارد.
5. **پایان**: پس از پایان با کلیک روی «باز کردن پوشه خروجی» به فایل‌های دانلود شده دسترسی پیدا کنید.

---

### 💻 رابط خط فرمان (CLI)

اجرای نسخه ترمینال:
```bash
python cli.py
# یا در صورت نصب پکیج:
aparat-dl
```

#### حالت تعاملی (Interactive)
در صورت اجرای برنامه بدون آرگومان، سیستم به صورت مرحله‌به‌مرحله ورودی‌های لازم را از شما می‌پرسد:
```bash
$ python cli.py

========================================================
         Aparat Downloader v1.0.0 - CLI Edition
               Maintained by Ali Bakhtiari
========================================================

Enter Aparat playlist / video URL or ID: 11402450
Fetching metadata...
Fetching qualities: [6/6]

Summary:
  Title:   مجموعه انیمیشن سریالی داستان های لاک پشت های نینجا
  Channel: اُمگا انیمیشن | Omega_Animation
  Type:    Playlist (6 videos)

#   | Duration | Qualities Available                 | Title
----+----------+-------------------------------------+-------------------------------
1   | 21:44    | 144p, 240p, 360p                    | قسمت ۱
2   | 22:44    | 144p, 240p, 360p                    | قسمت ۲
...

Available Qualities:
  [1] Best Available (Highest quality for each video) [Recommended]
  [2] 720p (with fallback to highest if unavailable)
  [3] 480p (with fallback)
Choice (1-5) [default: 1]: 1

Select Action:
  [1] Download video files directly
  [2] Export direct download links to a .txt file (for IDM / aria2)
Choice (1-2) [default: 1]: 1

Destination directory [default: ./Downloads]: ./Downloads
```

#### حالت پارامتری و خودکار (Scriptable)
می‌توانید تمام گزینه‌ها را در همان دستور مشخص کنید:

```bash
# دانلود کامل پلی‌لیست با کیفیت ۷۲۰ و فال‌بک خودکار
python cli.py 11402450 --quality 720 --dest ./my_videos

# دانلود تک ویدیو با بهترین کیفیت موجود
python cli.py https://www.aparat.com/v/nbl9l8o -q best

# استخراج فایل txt شامل تمام لینک‌ها برای IDM یا سرور دانلود
python cli.py 11402450 -q 720 --export --dest ./links

# استخراج لینک مستقیم تک ویدیو
python cli.py nbl9l8o --export
```

#### جدول گزینه‌های خط فرمان

| گزینه | سوییچ کوتاه | توضیحات | مقدار پیش‌فرض |
| :--- | :--- | :--- | :--- |
| `url_or_id` | | شناسه یا آدرس کامل ویدیو یا پلی‌لیست | درخواست تعاملی |
| `--quality` | `-q` | کیفیت مورد نظر (`1080`، `720`، `480`، `360`، `best`) | درخواست تعاملی |
| `--export` | `-e` | استخراج لینک‌ها در فایل متنی بجای دانلود | `False` |
| `--dest` | `-d` | پوشه مقصد برای ذخیره ویدیوها یا فایل متنی لینک‌ها | `./Downloads` |
| `--help` | `-h` | نمایش راهنمای دستورات خط فرمان | |

---

## 🐍 استفاده برنامه‌نویسی در پایتون (Python API)

می‌توانید هسته دانلودر را مستقیماً در پروژه‌های پایتون خود استفاده کنید:

```python
from core import AparatClient, parse_aparat_input

client = AparatClient()

# ۱. تجزیه ورودی (شناسه یا آدرس اینترنتی)
target_type, identifier = parse_aparat_input("https://www.aparat.com/playlist/11402450")

# ۲. دریافت متادیتا و اطلاعات پایه
data = client.fetch_target(identifier, target_type)
print(f"عنوان: {data['title']}")
print(f"تعداد ویدیوها: {len(data['videos'])}")

# ۳. دریافت کیفیت تمام ویدیوها به صورت موازی
client.fetch_all_video_qualities(
    data["videos"],
    max_workers=5,
    progress_cb=lambda done, tot: print(f"دریافت کیفیت {done} از {tot}")
)

# ۴. استخراج لینک‌ها به فایل متنی
client.export_links_to_txt(
    videos=data["videos"],
    preferred_quality="720",
    output_file="./links.txt"
)

# ۵. یا دانلود مستقیم ویدیو با نوار پیشرفت
video = data["videos"][0]
url, profile, is_fallback = client.resolve_download_link(video, preferred_quality="720")

def on_progress(downloaded_bytes, total_bytes, speed):
    percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
    print(f"\rپیشرفت: {percent:.1f}% با سرعت {speed / 1024 / 1024:.2f} مگابایت بر ثانیه", end="")

client.download_video(url, f"./{video['title']}.mp4", progress_callback=on_progress)
```

---

## 📁 ساختار فایل‌های پروژه

```
aparat_playlist_downloader/
├── core.py                 # هسته اصلی: ارتباط با API، دانلود استریم، تفکیک کیفیت و مالتی‌تردینگ
├── cli.py                  # واسط خط فرمان: نمایش تعاملی، جدول ویدیوها و نوار وضعیت
├── gui.py                  # واسط گرافیکی PyQt5: قالب تیره، راست‌به‌چپ (RTL) و دو نوار پیشرفت
├── test_core.py            # تست‌های واحد هسته برنامه
├── test_cli.py             # تست‌های واحد نسخه خط فرمان
├── test_gui.py             # تست‌های واحد نسخه گرافیکی
├── requirements.txt        # وابستگی‌های کامل (PyQt5 و requests)
├── cli_requirements.txt    # وابستگی‌های حداقلی ترمینال (فقط requests)
├── pyproject.toml          # پیکربندی پکیج و میانبرهای اجرایی (aparat-dl و aparat-gui)
├── LICENSE                 # مجوز انتشار نرم‌افزار (MIT)
├── README.md               # مستندات به زبان انگلیسی
└── README.fa.md            # مستندات جامع به زبان فارسی
```

---

## 🤝 مشارکت در توسعه

از هرگونه گزارش مشکل، پیشنهاد قابلیت جدید یا پول ریکوئست استقبال می‌شود!
1. پروژه را **Fork** کنید.
2. یک برنچ جدید برای قابلیت خود بسازید (`git checkout -b feature/NewFeature`).
3. تغییرات خود را ثبت (Commit) کنید (`git commit -m 'Add NewFeature'`).
4. تغییرات را به ریپازیتوری خود Push کنید (`git push origin feature/NewFeature`).
5. یک **Pull Request** ارسال نمایید.

---

## 👤 نویسنده و توسعه‌دهنده

طراحی و توسعه توسط **علی بختیاری** ([@alibakhtiari](https://github.com/alibakhtiari)).

---

## 📄 مجوز (License)

این پروژه یک نرم‌افزار آزاد و متن‌باز تحت مجوز [MIT License](LICENSE) است.
