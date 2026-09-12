# Design Specification: Aparat Playlist & Video Downloader v2.0

- **Maintainer / Author**: Ali Bakhtiari ([ali-0315](https://github.com/ali-0315))
- **Date**: 2026-09-12
- **Status**: Approved
- **Version**: 2.0.0

---

## 1. Overview & Goals

The goal of this project is to modernize and expand `aparat_playlist_downloader` into a robust, high-performance, and publicly maintained CLI and GUI tool for downloading videos and playlists from Aparat (`aparat.com`), maintained by **Ali Bakhtiari**.

### Key Objectives:
1. **Universal URL & ID Support**: Seamlessly accept both Playlists and Single Videos from raw IDs/hashes or full URLs (with or without trailing slashes and query parameters):
   - Playlist URL: `https://www.aparat.com/playlist/11402450/` or `https://www.aparat.com/playlist/11402450`
   - Playlist ID: `11402450`
   - Video URL: `https://www.aparat.com/v/nbl9l8o`
   - Video Hash: `nbl9l8o`
2. **Dynamic Quality Discovery**:
   - Fetch video list and all available qualities concurrently (via `ThreadPoolExecutor`), avoiding long sequential network wait times.
   - Detect mixed qualities across episodes (for example, in playlist `11402450`, episodes 1 & 2 have max 360p while episodes 3–5 have 720p).
3. **Smart Quality Resolution & Fallback**:
   - Offer `"Best Available"` (highest resolution for each individual video).
   - When a specific resolution (e.g. `720p`) is selected, download that quality if present; if missing on an episode, automatically fall back to its highest available quality.
4. **Download & Link Export**:
   - Option to download MP4 files directly to a chosen folder.
   - Option to export direct download URLs to a formatted `.txt` file (compatible with IDM, aria2, wget, etc.).
5. **Real-time Download Tracking**:
   - Live download progress bar with percentage, speed (MB/s), and downloaded/total size for both CLI and GUI.
6. **Fresh Ownership & Clean Repository**:
   - Fresh Git commit history authored by Ali Bakhtiari.
   - MIT License credited to Ali Bakhtiari.
   - Comprehensive `.gitignore`, modern `requirements.txt`, `cli_requirements.txt`, and `pyproject.toml`.
   - Updated bilingual documentation (`README.md` and `README.fa.md`).

---

## 2. Architecture & Modules

### 2.1 Project Layout
```text
aparat_playlist_downloader/
├── core.py                 # Core API client, URL parser, quality resolver, and downloader
├── cli.py                  # Interactive CLI with rich formatted table and progress bar
├── gui.py                  # Modern PyQt5 GUI with RTL support, video table & dual progress bars
├── download-icon.png       # Application icon
├── requirements.txt        # Full requirements (GUI + CLI)
├── cli_requirements.txt    # Minimal requirements (CLI only)
├── pyproject.toml          # Package metadata and console entry points
├── .gitignore              # Python, OS, IDE, and download ignores
├── LICENSE                 # MIT License (Ali Bakhtiari)
└── README.md               # Documentation & usage guide
```

---

### 2.2 Core Engine (`core.py`)

#### `TargetType` & `InputParser`
- `parse_aparat_input(input_str: str) -> (target_type: str, identifier: str)`:
  - Detects whether input is `'playlist'` or `'video'`.
  - Cleans input: trims whitespace, removes URL parameters (`?key=val`), removes trailing slashes.
  - Recognizes `/playlist/(\d+)`, `/v/([a-zA-Z0-9]+)`, pure digits (`\d+` as playlist), or alphanumeric hash (`[a-zA-Z0-9]{7}` as video).

#### `AparatClient`
- `fetch_target(identifier: str, target_type: str) -> dict`:
  - If `playlist`:
    - Queries `https://www.aparat.com/api/fa/v1/video/playlist/one/playlist_id/{playlist_id}`.
    - Follows pagination (`link_next`) if multiple pages exist.
    - Extracts playlist title, channel name, and list of `Video` items.
  - If `video`:
    - Queries `https://www.aparat.com/api/fa/v1/video/video/show/videohash/{video_uid}`.
    - Wraps single video into uniform data structure (playlist title = video title, 1 video item).
- `fetch_all_video_qualities(videos: list, max_workers: int = 5) -> list[dict]`:
  - Uses `ThreadPoolExecutor` to fetch `file_link_all` for all videos concurrently.
  - Stores available profiles (e.g. `144p`, `240p`, `360p`, `480p`, `720p`, `1080p`) and URLs on each video object.
- `extract_available_qualities(videos_details: list) -> list[str]`:
  - Gathers all unique profile tags present across the videos, sorted by resolution descending (e.g. `['1080p', '720p', '480p', '360p', '240p', '144p']`).
- `resolve_download_link(video: dict, preferred_quality: str) -> dict`:
  - If `preferred_quality == 'best'`, selects the highest profile available for the video.
  - If `preferred_quality` matches a profile on the video, selects it.
  - Fallback: Selects the highest available profile for that video, marking `is_fallback = True`.
- `download_file(url: str, output_path: str, progress_callback=None, cancel_token=None)`:
  - Streams response with `chunk_size=65536` (64KB).
  - Emits: `(bytes_downloaded, total_bytes, speed_bytes_per_sec)`.
  - Respects cancellation flag.
- `export_links_to_txt(items: list, output_file: str)`:
  - Writes formatted text file with URLs and comments.

---

### 2.3 Command Line Interface (`cli.py`)

- **Interactive Steps**:
  1. Header banner with maintainer credit (Ali Bakhtiari).
  2. Input prompt accepting playlist/video URL or ID.
  3. Fetch status with fast concurrent quality resolution.
  4. Formatted summary (Title, Channel, Total Videos).
  5. Video listing table showing Index, Title, Duration, and Available Qualities.
  6. Menu selection for Quality (Best Available, 720p, 480p, etc.).
  7. Menu selection for Action (`1: Download`, `2: Export .txt`).
  8. Destination folder prompt (default `./Downloads`).
  9. Execution:
     - Real-time download progress bar (`[████████░░] 65% | 18.5/28.4 MB | 2.1 MB/s | Ep 1`).
     - Or immediate `.txt` file export confirmation.

---

### 2.4 Graphical User Interface (`gui.py`)

- Built with **PyQt5** with clean modern styling, Fusion theme, and RTL support for Persian text.
- **Components**:
  1. **Input Section**:
     - QLineEdit for URL/ID with validation styling (neutral, active, error).
     - QPushButton "دریافت اطلاعات" (Fetch Info).
  2. **Metadata & Video Table**:
     - Info cards: Title, Channel, Total Count, Type (لیست پخش / ویدیو).
     - QTableWidget: Columns for `#`, `عنوان ویدیو (Title)`, `مدت زمان (Duration)`, `کیفیت‌های موجود (Available Qualities)`.
  3. **Options Section**:
     - Quality QComboBox: populated with detected qualities + "بهترین کیفیت ممکن (Best Available)".
     - Operation QComboBox: "دانلود ویدیوها (Download)" / "استخراج لینک‌ها (Export .txt)".
     - Destination QLineEdit + Browse QPushButton.
     - Action buttons: "شروع عملیات" (Start) and "توقف" (Cancel).
  4. **Progress Section**:
     - Dual QProgressBar:
       - Overall Progress (e.g. Video 3 of 6).
       - Current Video Progress (0% to 100%, speed, downloaded MB/total MB).
     - Status notification with "نمایش در پوشه" (Open Folder).
  5. **Worker Threading**:
     - Background `QThread` for fetching metadata.
     - Background `QThread` for downloading/exporting with clean signal/slot communication to keep the UI smooth and responsive.

---

## 3. Git Reset & Repository Maintenance

1. Remove any junk or untracked directories (`batwheels/`, `__pycache__/`).
2. Add full `.gitignore`.
3. Create MIT `LICENSE` with Ali Bakhtiari.
4. Update `pyproject.toml`, `requirements.txt`, and `cli_requirements.txt`.
5. Re-initialize Git repository:
   - Create a clean orphan branch / fresh commit history.
   - Commit all modernized files as the initial commit authored by `Ali Bakhtiari <as7490226@gmail.com>`.
   - Maintain remote `origin` pointing to `https://github.com/ali-0315/aparat_playlist_downloader.git`.

---

## 4. Verification & Testing Plan

1. **Unit & Logic Tests**:
   - Test `parse_aparat_input` with playlist URLs, playlist IDs, video URLs, video hashes, trailing slashes, and query parameters.
   - Test `resolve_download_link` with exact matches, fallback behavior, and best quality.
2. **Live Integration Tests**:
   - Test playlist `11402450` (`https://www.aparat.com/playlist/11402450/`):
     - Verify 6 videos fetched.
     - Verify detected qualities: `144p`, `240p`, `360p`, `480p`, `720p`.
     - Verify link export to `.txt`.
     - Verify video download streaming and progress callback.
   - Test single video `nbl9l8o` (`https://www.aparat.com/v/nbl9l8o`):
     - Verify 1 video fetched with its qualities (`144p`, `240p`, `360p`).
     - Verify link export and download.
3. **GUI Verification**:
   - Run GUI, test input loading, table population, and quality dropdown updates.
