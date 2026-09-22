# دانلودر ویدیو و لیست پخش آپارات (Aparat Downloader v1.0.0)

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)](https://github.com/alibakhtiari/aparat_playlist_downloader)
[![Website](https://img.shields.io/badge/Website-aliib.ir-007acc?style=flat&logo=googlechrome&logoColor=white)](https://aliib.ir)
[![WebABC](https://img.shields.io/badge/Agency-webabc.ir-ff5722?style=flat&logo=firefox&logoColor=white)](https://webabc.ir)

**ابزار حرفه‌ای، پرسرعت و مدرن برای دانلود ویدیوها و لیست‌های پخش (پلی‌لیست) آپارات به همراه رابط گرافیکی (GUI) و خط فرمان (CLI) با پشتیبانی از استخراج لینک برای IDM.**

[English](README.md) | [فارسی](README.fa.md)

</div>

---

## 📑 فهرست مطالب
- [معرفی و کاربرد](#-معرفی-پروژه)
- [ویژگی‌ها و قابلیت‌های کلیدی](#-قابلیت‌ها-و-ویژگی‌های-کلیدی)
- [فرمت‌های ورودی مجاز](#-نمونه-فرمت‌های-ورودی-مجاز)
- [راهنمای نصب](#-پیش‌نیازها-و-نحوه-نصب)
  - [نسخه بدون نیاز به نصب (Executable)](#فایل‌های-آماده-اجرا-بدون-نیاز-به-نصب-پایتون-portable-executables)
  - [اجرا از روی سورس‌کد پایتون](#پیش‌نیازها-اجرا-از-طریق-سورس‌کد-پایتون)
- [راهنمای استفاده](#-راهنمای-استفاده)
  - [رابط گرافیکی (GUI)](#️-رابط-کاربری-گرافیکی-gui)
  - [خط فرمان (CLI)](#-رابط-خط-فرمان-cli)
- [نمونه استفاده برنامه‌نویسی (Python API)](#-نمونه-استفاده-برنامه‌نویسی-python-api)
- [ساختار فایل‌های پروژه](#-ساختار-فایل‌های-پروژه)
- [اجرای تست‌ها](#-اجرای-تست‌های-واحد)
- [مشارکت در پروژه](#-مشارکت-در-توسعه)
- [توسعه‌دهنده و راه‌های ارتباطی](#-نویسنده-و-توسعه‌دهنده)
- [مجوز](#-مجوز-license)

---

## 🔎 معرفی پروژه

**دانلودر آپارات (Aparat Playlist & Video Downloader)** یک راه‌حل جامع، پایدار و کامل برای دانلود خودکار محتوا از سرویس آپارات (بزرگ‌ترین پلتفرم اشتراک ویدیو در ایران) است. این نرم‌افزار برای اهدافی مانند آرشیو دوره‌های آموزشی، دانلود گروهی مجموعه‌های ویدیویی و استخراج مستقیم لینک‌های دانلود پرسرعت بدون واترمارک و بدون افت کیفیت طراحی شده است.

کاربران می‌توانند هم از **رابط گرافیکی مدرن و راست‌به‌چپ (RTL)** با تم تاریک لذت ببرند و هم در سرورها یا ترمینال از **نسخه خط فرمان قدرتمند و تعاملی** استفاده نمایند.

---

## 🌟 قابلیت‌ها و ویژگی‌های کلیدی

- **پشتیبانی سراسری از ورودی‌ها**: پردازش هوشمند هر دو نوع ورودی: **لیست پخش (پلی‌لیست)** با شناسه عددی یا لینک کامل و **تک ویدیو** با کد هش یا آدرس وب‌سایت.
- **استعلام موازی کیفیت‌ها (Multi-threading)**: استخراج فوق‌العاده سریع لیست کیفیت‌های تمام ویدیوهای موجود در یک لیست پخش با کمک `ThreadPoolExecutor`.
- **فال‌بک هوشمند کیفیت (Smart Quality Fallback)**: انتخاب کیفیت دلخواه (`1080p`، `720p`، `480p`، `360p` یا `best`). چنانچه ویدیویی در لیست کیفیت انتخابی شما را نداشته باشد، به جای توقف فرآیند، برنامه بالاترین کیفیت ممکن آن ویدیو را دانلود می‌کند.
- **نوارهای پیشرفت زنده و نمایش سرعت لحظه‌ای**: نوار پیشرفت متنی در ترمینال با کاراکترهای یونیکد، نمایش درصد، سرعت لحظه‌ای بر حسب مگابایت بر ثانیه (MB/s) و دو نوار پیشرفت مجزا در رابط گرافیکی (یکی برای کل مجموعه و دیگری برای فایل جاری).
- **خروجی اختصاصی برای دانلود منیجرها**: تولید فایل متنی `.txt` تمیز شامل لینک‌های مستقیم CDN آپارات به همراه نام ویدیوها، آماده برای درون‌ریزی دسته‌ای (Batch Import) در دانلود منیجرهایی مانند Internet Download Manager (IDM)، aria2، curl و wget.
- **رابط گرافیکی مدرن (PyQt5 Fusion Dark)**: طراحی چشم‌نواز با چیدمان اصولی فارسی و راست‌به‌چپ (RTL)، جدول جزئیات ویدیوها، امکان انتخاب مسیر ذخیره‌سازی، توقف امن دانلود و دکمه باز کردن پوشه خروجی پس از اتمام.
- **نسخه خط فرمان منعطف و اسکریپت‌پذیر (CLI)**: دارای منوی راهنمای مرحله‌به‌مرحله به همراه فلگ‌های خط فرمان برای استفاده در اسکریپت‌ها، سرورهای لینوکسی و اتوماسیون.
- **کتابخانه پایتون استاندارد**: ماژولار با تایپ هینت‌های کامل جهت استفاده برنامه‌نویسان در قالب کلاس `AparatClient`.

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
نسخه‌های باینری کامپایل‌شده برای سیستم‌عامل‌های **ویندوز**، **لینوکس** و **مک** در بخش ریلیزهای گیت‌هاب منتشر می‌شوند:
- به صفحه **[GitHub Releases](https://github.com/alibakhtiari/aparat_playlist_downloader/releases)** بروید.
- فایل مناسب با سیستم‌عامل خود را دریافت کنید:
  - **ویندوز (x86_64)**: `aparat-dl-windows-amd64.exe` (خط فرمان) و `aparat-gui-windows-amd64.exe` (گرافیکی)
  - **لینوکس (x86_64)**: `aparat-dl-linux-amd64` (خط فرمان) و `aparat-gui-linux-amd64` (گرافیکی)
  - **مک‌اواس (Apple Silicon arm64)**: `aparat-dl-macos-arm64` (خط فرمان) و `aparat-gui-macos-arm64` (گرافیکی)
  - **مک‌اواس (Intel x86_64)**: `aparat-dl-macos-x86_64` (خط فرمان) و `aparat-gui-macos-x86_64` (گرافیکی)
- بدون نیاز به نصب پایتون و وابستگی‌ها به راحتی اجرا نمایید!

### پیش‌نیازها (اجرا از طریق سورس‌کد پایتون)
- پایتون ۳.۸ یا بالاتر (Python >= 3.8)
- مدیریت پکیج `pip`
- اتصال اینترنت

### ۱. کلون مخزن گیت
```bash
git clone https://github.com/alibakhtiari/aparat_playlist_downloader.git
cd aparat_playlist_downloader
```

### ۲. نصب پکیج‌ها و وابستگی‌ها

**نصب کامل (رابط گرافیکی + خط فرمان):**
```bash
pip install -r requirements.txt
```
*یا نصب به عنوان پکیج در حالت editable برای رجیستر شدن دستورات `aparat-dl` و `aparat-gui`:*
```bash
pip install -e .
```

**نصب نسخه کم‌حجم برای سرورها و ترمینال (فقط CLI بدون نیاز به رابط گرافیکی):**
```bash
pip install -r cli_requirements.txt
```

---

## 🚀 راهنمای استفاده

### 🖥️ رابط کاربری گرافیکی (GUI)

اجرای نسخه گرافیکی:
```bash
python gui.py
# یا در صورت نصب پکیج:
aparat-gui
```

#### مراحل استفاده در محیط گرافیکی:
1. **ورود اطلاعات**: شناسه عددی پلی‌لیست، هش ویدیو یا لینک را در فیلد مربوطه وارد کنید.
2. **دریافت اطلاعات**: بر روی دکمه **دریافت اطلاعات** کلیک نمایید. عنوان، کانال، تعداد قسمت‌ها و کیفیت‌های موجود دریافت می‌شوند.
3. **تنظیمات**:
   - کیفیت مورد نظر خود را مشخص کنید (`بهترین کیفیت ممکن`، `1080p`، `720p` و...).
   - نوع عملیات را مشخص کنید: `دانلود مستقیم ویدیوها` یا `استخراج لینک‌ها (.txt)`.
   - پوشه ذخیره‌سازی را انتخاب کنید.
4. **شروع عملیات**: با کلیک روی دکمه **شروع عملیات**، پیشرفت لحظه‌ای و سرعت دانلود را مشاهده کنید. در هر مرحله امکان لغو عملیات وجود دارد.
5. **پایان**: با کلیک بر روی دکمه **باز کردن پوشه خروجی**، فایل‌های ذخیره‌شده را مشاهده نمایید.

---

### 💻 رابط خط فرمان (CLI)

اجرا از طریق پایتون یا دستور مستقیم:
```bash
python cli.py
# یا در صورت نصب پکیج:
aparat-dl
```

#### حالت تعاملی (Interactive Mode)
در صورت اجرای بدون آرگومان، یک راهنمای ساده گام‌به‌گام شما را هدایت می‌کند:
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

#### حالت اجرای مستقیم با آرگومان‌ها (Scriptable / Batch Mode)
برای اسکریپت‌نویسی و اجرای بدون معطلی از سوییچ‌ها استفاده کنید:

```bash
# دانلود پلی‌لیست با کیفیت 720p و فال‌بک خودکار
python cli.py 11402450 --quality 720 --dest ./my_videos

# دانلود تک ویدیو با بالاترین کیفیت ممکن
python cli.py https://www.aparat.com/v/nbl9l8o -q best

# استخراج لیست لینک‌های مستقیم در یک فایل txt برای IDM
python cli.py 11402450 -q 720 --export --dest ./links

# استخراج لینک مستقیم برای تک ویدیو
python cli.py nbl9l8o --export
```

#### جدول راهنمای پارامترهای CLI

| پارامتر | سوییچ کوتاه | توضیحات | مقدار پیش‌فرض |
| :--- | :--- | :--- | :--- |
| `url_or_id` | | آدرس یا شناسه عددی پلی‌لیست یا ویدیو | دریافت از کاربر |
| `--quality` | `-q` | کیفیت هدف (`1080`, `720`, `480`, `360`, `best`) | دریافت از کاربر |
| `--export` | `-e` | استخراج لینک‌ها در قالب فایل متنی به جای دانلود | `False` |
| `--dest` | `-d` | مسیر پوشه مقصد برای ذخیره ویدیوها یا فایل متنی | `./Downloads` |
| `--help` | `-h` | نمایش پیام راهنما و پارامترها | |

---

## 🐍 نمونه استفاده برنامه‌نویسی (Python API)

شما می‌توانید ماژول‌های دانلودر را در پروژه‌های پایتونی خود به کار ببرید:

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
├── tests/                  # پوشه تست‌های واحد (شامل ۸۱ تست خودکار)
│   ├── __init__.py         # پکیج تست
│   ├── test_core.py        # تست‌های موتور اصلی و تجزیه‌کننده
│   ├── test_cli.py         # تست‌های نسخه ترمینال
│   └── test_gui.py         # تست‌های نسخه گرافیکی
├── requirements.txt        # وابستگی‌های کامل (PyQt5 و requests)
├── cli_requirements.txt    # وابستگی‌های حداقلی ترمینال (فقط requests)
├── pyproject.toml          # پیکربندی پکیج و میانبرهای اجرایی (aparat-dl و aparat-gui)
├── download-icon.png       # آیکون برنامه
├── LICENSE                 # مجوز انتشار نرم‌افزار (MIT)
├── README.md               # مستندات به زبان انگلیسی
└── README.fa.md            # مستندات جامع به زبان فارسی
```

---

## 🧪 اجرای تست‌های واحد

مجموعه تست‌های این پروژه شامل ۸۱ تست خودکار است که بخش‌های مختلف شامل مدیریت خطا، تطبیق کیفیت، دانلود قطعه‌ای، تبدیل نام فایل و رابط‌های کاربری را ارزیابی می‌کنند:

```bash
# اجرای تمامی تست‌ها
python -m pytest

# اجرای تست‌ها با جزئیات کامل
python -m pytest -v
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

طراحی و توسعه با ❤️ توسط **علی بختیاری** ([@alibakhtiari](https://github.com/alibakhtiari)).

- 🌐 **وب‌سایت شخصی و رزومه**: [aliib.ir](https://aliib.ir)
- 🚀 **طراحی وب‌سایت و راهکارهای دیجیتال**: [webabc.ir](https://webabc.ir)
- 🐙 **پروفایل گیت‌هاب**: [@alibakhtiari](https://github.com/alibakhtiari)

---

## 🏷️ کلیدواژه‌ها و برچسب‌های سئو (SEO Tags)

`دانلودر آپارات` `دانلود پلی لیست آپارات` `دانلود لیست پخش آپارات` `دانلود ویدیو آپارات` `استخراج لینک مستقیم آپارات` `دانلود با کیفیت 1080p` `دانلودر پایتون` `دانلودر رایگان آپارات` `دانلود دسته جمعی با IDM` `aparat downloader` `aparat playlist downloader`

---

## 📄 مجوز (License)

این پروژه یک نرم‌افزار آزاد و متن‌باز تحت مجوز [MIT License](LICENSE) است.
