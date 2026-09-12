# Aparat Playlist & Video Downloader v1.0.0

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![PyQt5](https://img.shields.io/badge/GUI-PyQt5-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Version](https://img.shields.io/badge/Version-1.0.0-blue.svg)](pyproject.toml)
[![Platform](https://img.shields.io/badge/Platform-Windows%20|%20Linux%20|%20macOS-lightgrey.svg)](https://github.com/alibakhtiari/aparat_playlist_downloader)

**A modern, blazing-fast CLI and GUI downloader for Aparat videos and playlists.**

[English](README.md) | [فارسی](README.fa.md)

</div>

---

## 🌟 Features

- **Universal Target Support**: Seamlessly download or export both **playlists** (by numeric ID or full URL) and **single videos** (by alphanumeric hash or full URL).
- **Concurrent Quality Detection**: Parallel resolution across playlist videos using multi-threaded workers (`ThreadPoolExecutor`) for near-instant metadata inspection.
- **Smart Quality Fallback**: Choose your preferred quality (`1080p`, `720p`, `480p`, `360p`, or `best`). If a video lacks your requested resolution, the engine automatically selects the highest available resolution without stopping the queue.
- **Real-Time Progress & Speed**: Dynamic streaming progress bars in both CLI (clean in-place unicode bar with live transfer rate and byte counters) and GUI (dual-progress bars for overall queue and active file).
- **Export Links for Download Managers**: Generate clean `.txt` files containing direct CDN download links and video titles, ready for batch import into Internet Download Manager (IDM), aria2, wget, or curl.
- **Modern Persian RTL GUI**: Beautiful PyQt5 dark Fusion interface built natively with Right-to-Left (RTL) Persian layout, interactive video table, destination browser, cancellation token support, and one-click folder opening.
- **Scriptable & Interactive CLI**: Use guided interactive prompts or automate downloads using command-line arguments. Works headless on servers without GUI dependencies.
- **Clean Python API**: Programmatic access through `AparatClient` with full typing annotations.

---

## 📋 Supported Input Formats

| Target Type | Input Format | Example |
| :--- | :--- | :--- |
| **Playlist** | Numeric ID | `11402450` |
| **Playlist** | Full URL | `https://www.aparat.com/playlist/11402450` |
| **Video** | Alphanumeric Hash | `nbl9l8o` |
| **Video** | Full URL | `https://www.aparat.com/v/nbl9l8o` |

---

## 📦 Installation

### Standalone Executables (No Python Required)
Pre-compiled standalone binaries for **Windows**, **Linux**, and **macOS** (both Apple Silicon and Intel) are automatically built and published for each release:
- Visit the **[GitHub Releases](https://github.com/alibakhtiari/aparat_playlist_downloader/releases)** page.
- Download the executable for your operating system:
  - **Windows (x86_64)**: `aparat-dl-windows-amd64.exe` (CLI), `aparat-gui-windows-amd64.exe` (GUI)
  - **Linux (x86_64)**: `aparat-dl-linux-amd64` (CLI), `aparat-gui-linux-amd64` (GUI)
  - **macOS (Apple Silicon arm64)**: `aparat-dl-macos-arm64` (CLI), `aparat-gui-macos-arm64` (GUI)
  - **macOS (Intel x86_64)**: `aparat-dl-macos-x86_64` (CLI), `aparat-gui-macos-x86_64` (GUI)
- Run directly without installing Python or dependencies!

### Prerequisites (Source Installation)
- Python 3.8 or higher
- `pip` (Python package manager)
- Active internet connection

### 1. Clone the Repository
```bash
git clone https://github.com/alibakhtiari/aparat_playlist_downloader.git
cd aparat_playlist_downloader
```

### 2. Install Dependencies

**Full Installation (CLI + GUI):**
```bash
pip install -r requirements.txt
```
*Or install in editable mode to register CLI commands (`aparat-dl` & `aparat-gui`):*
```bash
pip install -e .
```

**Headless / Server Installation (CLI Only, No GUI):**
```bash
pip install -r cli_requirements.txt
```

---

## 🚀 Usage

### 🖥️ Graphical User Interface (GUI)

Launch the modern PyQt5 interface:
```bash
python gui.py
# or if installed as package:
aparat-gui
```

#### GUI Workflow:
1. **Input**: Enter an Aparat playlist ID, video hash, or full URL.
2. **Fetch**: Click **دریافت اطلاعات** (Fetch Info). The application loads the title, channel name, video count, duration, and resolves available qualities.
3. **Configure**:
   - Choose your **Quality** (`Best Available`, `1080p`, `720p`, etc.)
   - Choose your **Action**: `دانلود ویدیوها` (Download Videos) or `استخراج لینک‌ها (.txt)` (Export Links)
   - Select your **Destination Folder**.
4. **Execute**: Click **شروع عملیات** (Start). Monitor dual progress bars (queue progress + per-file streaming speed). You can cancel anytime.
5. **Done**: Click **باز کردن پوشه خروجی** to immediately view downloaded files.

---

### 💻 Command Line Interface (CLI)

Run via script or registered command:
```bash
python cli.py
# or if installed as package:
aparat-dl
```

#### Interactive Mode
Simply run without arguments. The CLI will guide you step-by-step:
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
  ...
Choice (1-5) [default: 1]: 1

Select Action:
  [1] Download video files directly
  [2] Export direct download links to a .txt file (for IDM / aria2)
Choice (1-2) [default: 1]: 1

Destination directory [default: ./Downloads]: ./Downloads
```

#### Scriptable / Batch Mode
Provide flags to skip prompts and run directly:

```bash
# Download playlist in 720p with fallback
python cli.py 11402450 --quality 720 --dest ./my_videos

# Download single video with best available quality
python cli.py https://www.aparat.com/v/nbl9l8o -q best

# Export playlist direct links to a .txt file for IDM / aria2
python cli.py 11402450 -q 720 --export --dest ./links

# Export single video link
python cli.py nbl9l8o --export
```

#### CLI Options Reference

| Option | Short | Description | Default |
| :--- | :--- | :--- | :--- |
| `url_or_id` | | Playlist or video URL / ID | Interactive prompt |
| `--quality` | `-q` | Target resolution (`1080`, `720`, `480`, `360`, `best`) | Interactive prompt |
| `--export` | `-e` | Export direct links to `.txt` instead of downloading | `False` |
| `--dest` | `-d` | Destination directory for files or exported `.txt` | `./Downloads` |
| `--help` | `-h` | Display help message and options | |

---

## 🐍 Python API Usage

You can integrate Aparat Downloader into your own Python applications:

```python
from core import AparatClient, parse_aparat_input

client = AparatClient()

# 1. Parse user input
target_type, identifier = parse_aparat_input("https://www.aparat.com/playlist/11402450")

# 2. Fetch metadata
data = client.fetch_target(identifier, target_type)
print(f"Title: {data['title']}")
print(f"Total videos: {len(data['videos'])}")

# 3. Fetch qualities concurrently
client.fetch_all_video_qualities(
    data["videos"],
    max_workers=5,
    progress_cb=lambda done, tot: print(f"Resolved {done}/{tot}")
)

# 4. Export links to text file
client.export_links_to_txt(
    videos=data["videos"],
    preferred_quality="720",
    output_file="./links.txt"
)

# 5. Or download a specific video
video = data["videos"][0]
url, profile, is_fallback = client.resolve_download_link(video, preferred_quality="720")

def on_progress(downloaded_bytes, total_bytes, speed):
    percent = (downloaded_bytes / total_bytes * 100) if total_bytes > 0 else 0
    print(f"\rProgress: {percent:.1f}% @ {speed / 1024 / 1024:.2f} MB/s", end="")

client.download_video(url, f"./{video['title']}.mp4", progress_callback=on_progress)
```

---

## 📁 Project Structure

```
aparat_playlist_downloader/
├── core.py                 # Core engine: API client, concurrency, parser, streaming downloader
├── cli.py                  # CLI interface: interactive prompts, tables, progress bars
├── gui.py                  # GUI interface: PyQt5 modern dark UI with Persian RTL layout
├── test_core.py            # Unit tests for core engine (input parser, API, downloader)
├── test_cli.py             # Unit tests for CLI functions and arguments
├── test_gui.py             # Unit tests for GUI components and worker threads
├── requirements.txt        # Full dependencies (PyQt5, requests)
├── cli_requirements.txt    # Minimal CLI dependencies (requests only)
├── pyproject.toml          # Project package metadata & entry points (aparat-dl, aparat-gui)
├── LICENSE                 # MIT License
├── README.md               # English documentation
└── README.fa.md            # Persian documentation (راهنمای فارسی)
```

---

## 🤝 Contributing

Contributions, bug reports, and feature requests are welcome!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 👤 Author & Maintainer

Developed and maintained by **Ali Bakhtiari** ([@alibakhtiari](https://github.com/alibakhtiari)).


---

## 📄 License

This project is open-source software licensed under the [MIT License](LICENSE).