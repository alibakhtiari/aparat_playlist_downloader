# Aparat Playlist & Video Downloader v2.0 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize and clean the Aparat Downloader into a fast, reliable CLI and GUI application that supports both Aparat playlists (e.g. `11402450`) and single videos (e.g. `nbl9l8o`), discovers video qualities concurrently, enables quality selection with smart fallbacks, tracks live download progress, and is maintained under a fresh Git history authored by Ali Bakhtiari under the MIT License.

**Architecture:** A unified modular core (`core.py`) providing input parsing, multi-threaded metadata & quality discovery, smart quality selection with best-available fallback, and chunked streaming downloads with progress callbacks. The CLI (`cli.py`) and PyQt5 GUI (`gui.py`) consume the core client asynchronously for smooth, responsive user experiences.

**Tech Stack:** Python 3.8+, `requests`, `PyQt5`, `concurrent.futures`, `pytest`.

## Global Constraints
- Target platform: Windows, macOS, Linux
- Primary maintainer & copyright owner: Ali Bakhtiari (`ali-0315`)
- License: MIT
- Zero placeholders in tasks: all code, paths, and commands are fully specified.

---

### Task 1: Repository Cleanup, Packaging & License

**Files:**
- Create: `LICENSE`
- Create: `.gitignore`
- Create: `pyproject.toml`
- Modify: `requirements.txt`
- Modify: `cli_requirements.txt`
- Delete: `batwheels/` directory (empty artifact)

**Interfaces:**
- Produces: Clean dependency specifications (`requests>=2.28.0`, `PyQt5>=5.15.10`) and project metadata.

- [ ] **Step 1: Create comprehensive `.gitignore`**
  Add rules for Python cache, virtual environments, build artifacts, IDE files, and download outputs.
- [ ] **Step 2: Create MIT `LICENSE`**
  Set license to Ali Bakhtiari.
- [ ] **Step 3: Update `requirements.txt` and `cli_requirements.txt`**
  Use modern version constraints (`requests>=2.28.0`, `PyQt5>=5.15.10`).
- [ ] **Step 4: Create `pyproject.toml`**
  Define build system, project metadata, author Ali Bakhtiari, and CLI/GUI entry points.
- [ ] **Step 5: Remove stale directories**
  Remove `batwheels/` if it exists.
- [ ] **Step 6: Verify environment & dependencies**
  Run `python -c "import requests, PyQt5; print('Dependencies OK')"` to verify environment readiness.

---

### Task 2: Core Engine Implementation & Unit Tests (`core.py`)

**Files:**
- Modify: `core.py`
- Create: `test_core.py`

**Interfaces:**
- Produces:
  - `parse_aparat_input(input_str: str) -> tuple[str, str]` (target_type: 'playlist'|'video', identifier: str)
  - `sanitize_filename(name: str) -> str`
  - `AparatClient` class:
    - `fetch_info(identifier: str, target_type: str) -> dict`
    - `fetch_all_video_qualities(videos: list, max_workers: int = 5) -> list[dict]`
    - `get_available_qualities(videos: list) -> list[str]`
    - `resolve_download_link(video: dict, preferred_quality: str) -> tuple[str, str, bool]` (url, quality, is_fallback)
    - `download_video(url: str, output_path: str, progress_callback=None, cancel_token=None)`
    - `export_links_to_txt(videos: list, preferred_quality: str, output_file: str)`

- [ ] **Step 1: Write unit tests in `test_core.py` for input parsing and quality resolution**
  Test playlist URLs (`https://www.aparat.com/playlist/11402450/`, `https://www.aparat.com/playlist/11402450`), playlist IDs (`11402450`), video URLs (`https://www.aparat.com/v/nbl9l8o`), and video hashes (`nbl9l8o`). Test fallback quality selection.
- [ ] **Step 2: Run tests to verify failure**
  Run `pytest test_core.py` and confirm functions are missing.
- [ ] **Step 3: Implement `core.py`**
  Implement `parse_aparat_input`, `sanitize_filename`, and `AparatClient` with concurrent quality fetching and streaming download.
- [ ] **Step 4: Run unit tests to verify they pass**
  Run `pytest test_core.py -v`.
- [ ] **Step 5: Run live integration test against Aparat API**
  Fetch playlist `11402450`, verify 6 videos and qualities `['144p', '240p', '360p', '480p', '720p']`. Fetch video `nbl9l8o`, verify 1 video.

---

### Task 3: Interactive CLI Redesign (`cli.py`)

**Files:**
- Modify: `cli.py`

**Interfaces:**
- Consumes: `parse_aparat_input`, `AparatClient` from `core.py`
- Produces: Fully interactive CLI workflow with video table, quality choices, action choice, and live download progress bar.

- [ ] **Step 1: Implement terminal progress bar helper in `cli.py`**
  Format: `[████████░░] 80% (24.3/30.4 MB) - 3.2 MB/s`.
- [ ] **Step 2: Implement interactive CLI prompt sequence**
  - Accept URL or ID (playlist or single video).
  - Print playlist/video metadata summary.
  - Print formatted list of videos with durations and available profiles.
  - Prompt for Quality selection (Best Available, 720p, 480p, 360p, 240p, 144p).
  - Prompt for Action (1: Download, 2: Export links to .txt).
  - Prompt for Destination directory (defaults to `./Downloads`).
- [ ] **Step 3: Test CLI in dry-run/export mode**
  Run `python cli.py` with playlist `11402450` to export `.txt` links, verify the resulting file.

---

### Task 4: Modern PyQt5 GUI Redesign (`gui.py`)

**Files:**
- Modify: `gui.py`

**Interfaces:**
- Consumes: `parse_aparat_input`, `AparatClient` from `core.py`
- Produces: Modern PyQt5 GUI with RTL support, asynchronous fetching worker, video table, dynamic quality dropdown, dual progress bars, and cancel support.

- [ ] **Step 1: Refactor `DownloadWorker` and add `FetchInfoWorker` in `gui.py`**
  Ensure long-running network operations (fetching playlist details, concurrent qualities, downloading) run in background `QThread` instances without freezing the UI.
- [ ] **Step 2: Redesign GUI layout in `ModernApp`**
  - Top input bar: URL/ID text field + "دریافت اطلاعات" (Fetch) button.
  - Info card: Title, Channel, Total Videos count, Type badge.
  - Video table widget: `#`, `عنوان ویدیو (Title)`, `مدت زمان (Duration)`, `کیفیت‌های موجود (Available Qualities)`.
  - Config frame: Dynamic quality combobox, action combobox, destination folder picker with browse button.
  - Action buttons: "شروع عملیات" (Start) and "توقف" (Cancel).
  - Dual progress bars: Overall progress + current file download progress (with percentage, MBs, and speed).
- [ ] **Step 3: Test GUI initialization and signal wiring**
  Run a smoke test script to verify PyQt5 widgets initialize without errors.

---

### Task 5: Documentation & End-to-End Verification

**Files:**
- Modify: `README.md`
- Create: `README.fa.md`

**Interfaces:**
- Produces: Complete English and Persian documentation reflecting v2.0 features, usage, single video & playlist support, and author credits.

- [ ] **Step 1: Update `README.md`**
  Document features (playlist & single video support, dynamic qualities, best available fallback, live progress, link export), CLI usage, GUI usage, and author Ali Bakhtiari.
- [ ] **Step 2: Update/Create `README.fa.md`**
  Provide full Persian guide for Iranian developers and users.
- [ ] **Step 3: End-to-end verification**
  - Verify playlist `11402450` export to `.txt`.
  - Verify single video `nbl9l8o` export to `.txt`.
  - Verify download test (small clip or partial check).

---

### Task 6: Git History Reset & Fresh Ownership

**Files:**
- All repository files

- [ ] **Step 1: Check git status and stage all files**
- [ ] **Step 2: Reset git history into a single fresh initial commit**
  Create an orphan branch `fresh-main`, commit all files under `Ali Bakhtiari <as7490226@gmail.com>`, replace `main`, keeping the remote configured to `origin` (`ali-0315/aparat_playlist_downloader`).
- [ ] **Step 3: Verify git log**
  Confirm only the fresh initial commit exists authored by Ali Bakhtiari.
