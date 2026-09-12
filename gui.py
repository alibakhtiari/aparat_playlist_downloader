"""Modern PyQt5 Graphical Interface for Aparat Downloader v1.0.0.

Provides an RTL Persian interface with Fusion style, card-based layout,
dynamic quality detection, dual progress bars, and background worker threads.
Author: Ali Bakhtiari
"""

__version__ = "1.0.0"

import os
import platform
import subprocess
import sys
from typing import Any, Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core import (
    AparatClient,
    AparatDownloader,
    CancellationToken,
    export_links_to_txt,
    format_duration,
    get_available_qualities,
    parse_aparat_input,
    sanitize_filename,
)


def format_bytes(size: float) -> str:
    """Format bytes into human-readable representation."""
    if size < 0:
        return "0.0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(size) < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} PB"


def open_in_file_manager(folder_path: str) -> None:
    """Open folder in operating system's native file explorer."""
    if not os.path.exists(folder_path):
        return
    try:
        if platform.system() == "Windows":
            os.startfile(folder_path)
        elif platform.system() == "Darwin":
            subprocess.run(["open", folder_path], check=False)
        else:
            subprocess.run(["xdg-open", folder_path], check=False)
    except Exception:
        pass


class FetchTargetWorker(QThread):
    """Background worker to parse target and fetch video metadata and qualities."""

    progress = pyqtSignal(int, int)  # completed, total
    finished = pyqtSignal(dict)      # target data dict
    error = pyqtSignal(str)          # error message

    def __init__(self, target_input: str, client: Optional[AparatClient] = None) -> None:
        super().__init__()
        self.target_input = target_input
        self.client = client

    def run(self) -> None:
        try:
            cleaned_input = (self.target_input or "").strip()
            if not cleaned_input:
                self.error.emit("لطفاً لینک یا شناسه لیست پخش / ویدیو را وارد کنید.")
                return

            target_type, identifier = parse_aparat_input(cleaned_input)
            client = self.client or AparatClient()
            target_data = client.fetch_target(identifier, target_type)
            videos = target_data.get("videos", [])
            if not videos:
                self.error.emit("هیچ ویدیویی در این لیست پخش / شناسه یافت نشد.")
                return

            def on_progress(completed: int, total: int) -> None:
                self.progress.emit(completed, total)

            client.fetch_all_video_qualities(videos, progress_cb=on_progress)
            self.finished.emit(target_data)
        except Exception as e:
            self.error.emit(str(e))


class OperationWorker(QThread):
    """Background worker for downloading videos or exporting links with cancellation."""

    overall_progress = pyqtSignal(int, int, str)     # current_idx, total_videos, title
    file_progress = pyqtSignal(int, int, float)       # downloaded_bytes, total_bytes, speed
    finished = pyqtSignal(bool, str, str)             # success, message, output_folder

    def __init__(
        self,
        videos: List[Dict[str, Any]],
        preferred_quality: str,
        target_data: Dict[str, Any],
        destination_path: str,
        action: str = "download",
        client: Optional[AparatClient] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> None:
        super().__init__()
        self.videos = videos
        self.preferred_quality = preferred_quality
        self.target_data = target_data
        self.destination_path = destination_path
        self.action = action
        self.client = client
        self.cancel_token = cancel_token or CancellationToken()

    def run(self) -> None:
        try:
            client = self.client or AparatClient()
            cancel_token = self.cancel_token
            action = (self.action or "download").lower()

            if "export" in action or "استخراج" in action:
                os.makedirs(self.destination_path, exist_ok=True)
                raw_title = self.target_data.get("title") or "aparat_links"
                safe_title = sanitize_filename(raw_title)
                txt_path = os.path.join(self.destination_path, f"{safe_title}.txt")

                if cancel_token.is_cancelled():
                    self.finished.emit(False, "عملیات توسط کاربر متوقف شد.", self.destination_path)
                    return

                count = export_links_to_txt(self.videos, self.preferred_quality, txt_path)

                if cancel_token.is_cancelled():
                    self.finished.emit(False, "عملیات توسط کاربر متوقف شد.", self.destination_path)
                    return

                msg = f"تعداد {count} لینک با موفقیت در فایل '{os.path.basename(txt_path)}' ذخیره شد."
                self.finished.emit(True, msg, self.destination_path)
                return

            # Download mode
            target_type = self.target_data.get("type", "playlist")
            safe_target_title = sanitize_filename(self.target_data.get("title") or "aparat_videos")

            if target_type == "playlist":
                output_dir = os.path.join(self.destination_path, safe_target_title)
            else:
                output_dir = self.destination_path
            os.makedirs(output_dir, exist_ok=True)

            total_videos = len(self.videos)
            downloaded_count = 0
            failed_count = 0

            for idx, video in enumerate(self.videos, start=1):
                if cancel_token.is_cancelled():
                    self.finished.emit(False, "عملیات توسط کاربر متوقف شد.", output_dir)
                    return

                vid_title = sanitize_filename(video.get("title") or f"video_{idx}")
                self.overall_progress.emit(idx, total_videos, video.get("title") or f"ویدیو {idx}")

                try:
                    url, profile, is_fallback = client.resolve_download_link(
                        video, self.preferred_quality
                    )
                except Exception:
                    failed_count += 1
                    continue

                filename = f"{vid_title} - {profile}.mp4"
                filepath = os.path.join(output_dir, filename)

                def on_file_prog(curr: int, tot: int, spd: float) -> None:
                    self.file_progress.emit(curr, tot, spd)

                success = client.download_video(
                    url,
                    filepath,
                    progress_callback=on_file_prog,
                    cancel_token=cancel_token,
                )

                if cancel_token.is_cancelled():
                    self.finished.emit(False, "عملیات توسط کاربر متوقف شد.", output_dir)
                    return

                if success:
                    downloaded_count += 1
                else:
                    failed_count += 1

            if downloaded_count > 0:
                msg = f"دانلود {downloaded_count} از {total_videos} ویدیو با موفقیت به پایان رسید."
                if failed_count > 0:
                    msg += f" ({failed_count} مورد ناموفق)"
                self.finished.emit(True, msg, output_dir)
            else:
                self.finished.emit(False, "هیچ ویدیویی دانلود نشد.", output_dir)
        except Exception as e:
            self.finished.emit(False, f"خطا در انجام عملیات: {str(e)}", self.destination_path)


# Backward compatibility aliases
DownloadWorker = OperationWorker


class ModernApp(QMainWindow):
    """Modern Aparat Downloader GUI window."""

    def __init__(self) -> None:
        super().__init__()
        self.target_data: Optional[Dict[str, Any]] = None
        self.fetch_worker: Optional[FetchTargetWorker] = None
        self.operation_worker: Optional[OperationWorker] = None
        self.cancel_token: Optional[CancellationToken] = None

        self.init_ui()

    def init_ui(self) -> None:
        self.setWindowTitle("دانلودر ویدیو و لیست پخش آپارات v1.0.0 - علی بختیاری")
        self.setMinimumSize(820, 680)
        self.resize(880, 720)
        self.setLayoutDirection(Qt.RightToLeft)

        # Apply global application stylesheet
        self.setStyleSheet("""
        QMainWindow {
            background-color: #f8fafc;
        }
        QWidget {
            font-family: 'Vazirmatn', 'IRANSans', 'Segoe UI', 'Tahoma', sans-serif;
            font-size: 13px;
            color: #1e293b;
        }
        QFrame.card {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 10px;
        }
        QLabel {
            color: #334155;
        }
        QLineEdit {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 8px 12px;
            background-color: #ffffff;
            selection-background-color: #e11d48;
        }
        QLineEdit:focus {
            border: 1.5px solid #e11d48;
        }
        QComboBox {
            border: 1px solid #cbd5e1;
            border-radius: 6px;
            padding: 6px 12px;
            background-color: #ffffff;
            min-height: 24px;
        }
        QComboBox:hover {
            border: 1px solid #94a3b8;
        }
        QComboBox:focus {
            border: 1.5px solid #e11d48;
        }
        QPushButton {
            border-radius: 6px;
            padding: 8px 16px;
            font-weight: bold;
        }
        QPushButton#primaryBtn {
            background-color: #e11d48;
            color: #ffffff;
            border: none;
        }
        QPushButton#primaryBtn:hover {
            background-color: #be123c;
        }
        QPushButton#primaryBtn:pressed {
            background-color: #9f1239;
        }
        QPushButton#primaryBtn:disabled {
            background-color: #fda4af;
            color: #ffffff;
        }
        QPushButton#secondaryBtn {
            background-color: #f1f5f9;
            color: #334155;
            border: 1px solid #cbd5e1;
        }
        QPushButton#secondaryBtn:hover {
            background-color: #e2e8f0;
        }
        QPushButton#secondaryBtn:pressed {
            background-color: #cbd5e1;
        }
        QPushButton#cancelBtn {
            background-color: #ef4444;
            color: #ffffff;
            border: none;
        }
        QPushButton#cancelBtn:hover {
            background-color: #dc2626;
        }
        QPushButton#cancelBtn:pressed {
            background-color: #b91c1c;
        }
        QPushButton#cancelBtn:disabled {
            background-color: #fca5a5;
            color: #ffffff;
        }
        QTableWidget {
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            background-color: #ffffff;
            alternate-background-color: #f8fafc;
            gridline-color: #f1f5f9;
            selection-background-color: #ffe4e6;
            selection-color: #881337;
        }
        QHeaderView::section {
            background-color: #f1f5f9;
            color: #475569;
            font-weight: bold;
            padding: 8px;
            border: none;
            border-bottom: 2px solid #e2e8f0;
        }
        QProgressBar {
            border: 1px solid #e2e8f0;
            border-radius: 6px;
            text-align: center;
            background-color: #f1f5f9;
            height: 20px;
            font-size: 11px;
            font-weight: bold;
            color: #0f172a;
        }
        QProgressBar::chunk {
            background-color: #e11d48;
            border-radius: 5px;
        }
        """)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(12)

        # 1. Header Card
        header_card = QFrame()
        header_card.setProperty("class", "card")
        header_layout = QVBoxLayout(header_card)
        header_layout.setContentsMargins(16, 12, 16, 12)
        header_layout.setSpacing(4)

        header_title = QLabel("دانلودر ویدیو و لیست پخش آپارات")
        title_font = QFont("Vazirmatn", 15, QFont.Bold)
        header_title.setFont(title_font)
        header_title.setStyleSheet("color: #0f172a;")

        header_subtitle = QLabel("نسخه ۱.۰.۰ | توسعه داده شده توسط علی بختیاری (Ali Bakhtiari)")
        header_subtitle.setStyleSheet("color: #64748b; font-size: 11px;")

        header_layout.addWidget(header_title)
        header_layout.addWidget(header_subtitle)
        main_layout.addWidget(header_card)

        # 2. Input Card
        input_card = QFrame()
        input_card.setProperty("class", "card")
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 12, 16, 12)
        input_layout.setSpacing(8)

        input_label = QLabel("لینک یا شناسه لیست پخش / ویدیو را وارد کنید:")
        input_label.setStyleSheet("font-weight: bold; color: #1e293b;")

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.link_input = QLineEdit()
        self.link_input.setPlaceholderText(
            "نمونه: 11402450 یا https://www.aparat.com/playlist/11402450/ یا https://www.aparat.com/v/nbl9l8o"
        )
        self.link_input.returnPressed.connect(self.fetch_target_info)

        self.fetch_button = QPushButton("دریافت اطلاعات لیست / ویدیو")
        self.fetch_button.setObjectName("primaryBtn")
        self.fetch_button.setCursor(Qt.PointingHandCursor)
        self.fetch_button.clicked.connect(self.fetch_target_info)

        input_row.addWidget(self.link_input, stretch=4)
        input_row.addWidget(self.fetch_button, stretch=1)

        input_layout.addWidget(input_label)
        input_layout.addLayout(input_row)
        main_layout.addWidget(input_card)

        # 3. Summary & Video Table Card
        table_card = QFrame()
        table_card.setProperty("class", "card")
        table_layout = QVBoxLayout(table_card)
        table_layout.setContentsMargins(16, 12, 16, 12)
        table_layout.setSpacing(10)

        # Summary Info Row
        summary_row = QHBoxLayout()
        summary_row.setSpacing(16)

        self.summary_title_label = QLabel("عنوان: -")
        self.summary_title_label.setStyleSheet("font-weight: bold; color: #0f172a;")

        self.summary_channel_label = QLabel("کانال: -")
        self.summary_channel_label.setStyleSheet("color: #475569;")

        self.summary_type_label = QLabel("نوع: -")
        self.summary_type_label.setStyleSheet(
            "background-color: #f1f5f9; color: #334155; padding: 2px 8px; border-radius: 4px; font-weight: bold;"
        )

        self.summary_count_label = QLabel("تعداد: ۰ ویدیو")
        self.summary_count_label.setStyleSheet(
            "background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-weight: bold;"
        )

        summary_row.addWidget(self.summary_title_label, stretch=3)
        summary_row.addWidget(self.summary_channel_label, stretch=2)
        summary_row.addWidget(self.summary_type_label, stretch=1)
        summary_row.addWidget(self.summary_count_label, stretch=1)
        table_layout.addLayout(summary_row)

        # Video Table
        self.video_table = QTableWidget()
        self.video_table.setColumnCount(4)
        self.video_table.setHorizontalHeaderLabels(
            ["ردیف (#)", "عنوان ویدیو (Title)", "مدت زمان (Duration)", "کیفیت‌های موجود (Available Qualities)"]
        )
        self.video_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.video_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.video_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.video_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.video_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.video_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.video_table.setAlternatingRowColors(True)
        self.video_table.verticalHeader().setVisible(False)
        self.video_table.setMinimumHeight(180)

        table_layout.addWidget(self.video_table)
        main_layout.addWidget(table_card, stretch=1)

        # 4. Options Card
        options_card = QFrame()
        options_card.setProperty("class", "card")
        options_layout = QGridLayout(options_card)
        options_layout.setContentsMargins(16, 12, 16, 12)
        options_layout.setHorizontalSpacing(14)
        options_layout.setVerticalSpacing(8)

        # Quality & Action Dropdowns
        quality_label = QLabel("کیفیت دانلود:")
        quality_label.setStyleSheet("font-weight: bold;")
        self.quality_combo = QComboBox()
        self.quality_combo.addItem("بهترین کیفیت ممکن (Best Available)", userData="best")

        action_label = QLabel("نوع عملیات:")
        action_label.setStyleSheet("font-weight: bold;")
        self.action_combo = QComboBox()
        self.action_combo.addItem("دانلود ویدیوها", userData="download")
        self.action_combo.addItem("استخراج لینک‌ها به فایل txt", userData="export")

        options_layout.addWidget(quality_label, 0, 0)
        options_layout.addWidget(self.quality_combo, 0, 1)
        options_layout.addWidget(action_label, 0, 2)
        options_layout.addWidget(self.action_combo, 0, 3)

        # Destination Folder
        folder_label = QLabel("مسیر ذخیره‌سازی:")
        folder_label.setStyleSheet("font-weight: bold;")

        folder_row = QHBoxLayout()
        folder_row.setSpacing(8)

        default_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        if not os.path.exists(default_downloads):
            default_downloads = os.path.abspath("Downloads")

        self.folder_input = QLineEdit(default_downloads)
        self.browse_button = QPushButton("انتخاب پوشه...")
        self.browse_button.setObjectName("secondaryBtn")
        self.browse_button.setCursor(Qt.PointingHandCursor)
        self.browse_button.clicked.connect(self.browse_folder)

        folder_row.addWidget(self.folder_input, stretch=4)
        folder_row.addWidget(self.browse_button, stretch=1)

        options_layout.addWidget(folder_label, 1, 0)
        options_layout.addLayout(folder_row, 1, 1, 1, 3)

        main_layout.addWidget(options_card)

        # 5. Action & Progress Card
        action_card = QFrame()
        action_card.setProperty("class", "card")
        action_layout = QVBoxLayout(action_card)
        action_layout.setContentsMargins(16, 12, 16, 12)
        action_layout.setSpacing(8)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.start_button = QPushButton("شروع عملیات")
        self.start_button.setObjectName("primaryBtn")
        self.start_button.setMinimumHeight(40)
        self.start_button.setCursor(Qt.PointingHandCursor)
        self.start_button.clicked.connect(self.start_operation)

        self.cancel_button = QPushButton("توقف")
        self.cancel_button.setObjectName("cancelBtn")
        self.cancel_button.setMinimumHeight(40)
        self.cancel_button.setCursor(Qt.PointingHandCursor)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel_operation)

        btn_row.addWidget(self.start_button, stretch=4)
        btn_row.addWidget(self.cancel_button, stretch=1)
        action_layout.addLayout(btn_row)

        # Progress bars
        prog_grid = QGridLayout()
        prog_grid.setHorizontalSpacing(10)
        prog_grid.setVerticalSpacing(4)

        overall_lbl = QLabel("پیشرفت کلی:")
        overall_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        self.overall_progress_bar = QProgressBar()
        self.overall_progress_bar.setRange(0, 100)
        self.overall_progress_bar.setValue(0)

        file_lbl = QLabel("پیشرفت فایل:")
        file_lbl.setStyleSheet("font-size: 11px; color: #64748b;")
        self.file_progress_bar = QProgressBar()
        self.file_progress_bar.setRange(0, 100)
        self.file_progress_bar.setValue(0)

        prog_grid.addWidget(overall_lbl, 0, 0)
        prog_grid.addWidget(self.overall_progress_bar, 0, 1)
        prog_grid.addWidget(file_lbl, 1, 0)
        prog_grid.addWidget(self.file_progress_bar, 1, 1)

        action_layout.addLayout(prog_grid)

        # Status Label
        self.status_label = QLabel("آماده برای دریافت اطلاعات و شروع عملیات.")
        self.status_label.setStyleSheet("color: #475569; font-size: 11px; padding-top: 2px;")
        action_layout.addWidget(self.status_label)

        main_layout.addWidget(action_card)

    def fetch_target_info(self) -> None:
        """Initiate background fetch of target metadata and qualities."""
        raw_input = self.link_input.text().strip()
        if not raw_input:
            QMessageBox.warning(self, "خطا", "لطفاً لینک یا شناسه لیست پخش / ویدیو را وارد کنید.")
            return

        self.set_ui_busy(True, "fetch")
        self.status_label.setText("در حال ارتباط با آپارات و دریافت اطلاعات...")

        self.fetch_worker = FetchTargetWorker(raw_input)
        self.fetch_worker.progress.connect(self.on_fetch_progress)
        self.fetch_worker.finished.connect(self.on_fetch_finished)
        self.fetch_worker.error.connect(self.on_fetch_error)
        self.fetch_worker.start()

    def on_fetch_progress(self, completed: int, total: int) -> None:
        """Update status during video quality inspection."""
        self.status_label.setText(f"در حال دریافت کیفیت‌های موجود ویدیوها... ({completed} از {total})")

    def on_fetch_finished(self, data: Dict[str, Any]) -> None:
        """Handle successful target fetching."""
        self.target_data = data
        self.set_ui_busy(False)

        videos = data.get("videos", [])
        title = data.get("title", "-")
        channel = data.get("channel_name") or "-"
        target_type = "لیست پخش" if data.get("type") == "playlist" else "ویدیوی تکی"

        # Update Summary Labels
        self.summary_title_label.setText(f"عنوان: {title}")
        self.summary_channel_label.setText(f"کانال: {channel}")
        self.summary_type_label.setText(f"نوع: {target_type}")
        self.summary_count_label.setText(f"تعداد: {len(videos)} ویدیو")

        # Populate Video Table
        self.video_table.setRowCount(len(videos))
        for row, video in enumerate(videos):
            item_num = QTableWidgetItem(str(row + 1))
            item_num.setTextAlignment(Qt.AlignCenter)

            item_title = QTableWidgetItem(video.get("title", "untitled"))

            item_dur = QTableWidgetItem(video.get("duration_formatted", "00:00"))
            item_dur.setTextAlignment(Qt.AlignCenter)

            qualities_list = [
                q.get("profile") for q in video.get("qualities", []) if q.get("profile")
            ]
            item_qual = QTableWidgetItem(", ".join(qualities_list) if qualities_list else "نامشخص")
            item_qual.setTextAlignment(Qt.AlignCenter)

            self.video_table.setItem(row, 0, item_num)
            self.video_table.setItem(row, 1, item_title)
            self.video_table.setItem(row, 2, item_dur)
            self.video_table.setItem(row, 3, item_qual)

        # Populate Dynamic Quality ComboBox
        self.quality_combo.clear()
        self.quality_combo.addItem("بهترین کیفیت ممکن (Best Available)", userData="best")
        available_qualities = get_available_qualities(videos)
        for q in available_qualities:
            self.quality_combo.addItem(q, userData=q)

        self.status_label.setText(
            f"اطلاعات با موفقیت دریافت شد ({len(videos)} ویدیو). کیفیت و عملیات را انتخاب کرده و شروع را بزنید."
        )

    def on_fetch_error(self, err_msg: str) -> None:
        """Handle error while fetching target data."""
        self.set_ui_busy(False)
        self.status_label.setText(f"خطا در دریافت اطلاعات: {err_msg}")
        QMessageBox.warning(self, "خطا در دریافت اطلاعات", f"خطایی رخ داد:\n{err_msg}")

    def browse_folder(self) -> None:
        """Open directory chooser dialog."""
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه ذخیره‌سازی")
        if folder:
            self.folder_input.setText(folder)

    def start_operation(self) -> None:
        """Start downloading or exporting links."""
        if not self.target_data:
            QMessageBox.warning(
                self,
                "عدم وجود اطلاعات",
                "لطفاً ابتدا با کلیک روی 'دریافت اطلاعات لیست / ویدیو' اطلاعات را دریافت کنید.",
            )
            return

        dest_folder = self.folder_input.text().strip()
        if not dest_folder:
            QMessageBox.warning(self, "مسیر نامعتبر", "لطفاً یک پوشه مقصد معتبر انتخاب کنید.")
            return

        videos = self.target_data.get("videos", [])
        if not videos:
            QMessageBox.warning(self, "بدون ویدیو", "هیچ ویدیویی برای عملیات وجود ندارد.")
            return

        # Resolve selected quality
        selected_quality = self.quality_combo.currentData() or self.quality_combo.currentText()
        if "بهترین" in selected_quality or selected_quality.lower() == "best":
            preferred_quality = "best"
        else:
            preferred_quality = selected_quality

        # Resolve selected action
        selected_action = self.action_combo.currentData() or self.action_combo.currentText()
        action = "export" if ("export" in selected_action or "استخراج" in selected_action) else "download"

        # Update UI state
        self.set_ui_busy(True, "operation")
        self.overall_progress_bar.setRange(0, len(videos))
        self.overall_progress_bar.setValue(0)
        self.file_progress_bar.setValue(0)
        self.status_label.setText("در حال آغاز عملیات...")

        self.cancel_token = CancellationToken()
        self.operation_worker = OperationWorker(
            videos=videos,
            preferred_quality=preferred_quality,
            target_data=self.target_data,
            destination_path=dest_folder,
            action=action,
            cancel_token=self.cancel_token,
        )
        self.operation_worker.overall_progress.connect(self.on_overall_progress)
        self.operation_worker.file_progress.connect(self.on_file_progress)
        self.operation_worker.finished.connect(self.on_operation_finished)
        self.operation_worker.start()

    def cancel_operation(self) -> None:
        """Request cooperative cancellation."""
        if self.cancel_token:
            self.cancel_token.cancel()
            self.cancel_button.setEnabled(False)
            self.status_label.setText("در حال متوقف کردن عملیات...")

    def on_overall_progress(self, current_idx: int, total_items: int, title: str) -> None:
        """Update overall progress bar."""
        self.overall_progress_bar.setMaximum(total_items)
        self.overall_progress_bar.setValue(current_idx)
        self.status_label.setText(f"ویدیو {current_idx} از {total_items}: {title}")

    def on_file_progress(self, current_bytes: int, total_bytes: int, speed: float) -> None:
        """Update per-file download progress bar."""
        if total_bytes > 0:
            percent = int((current_bytes / total_bytes) * 100)
            self.file_progress_bar.setValue(percent)
            curr_str = format_bytes(current_bytes)
            tot_str = format_bytes(total_bytes)
            spd_str = f"{format_bytes(speed)}/s"
            self.status_label.setText(f"{percent}% ({curr_str} / {tot_str}) - {spd_str}")
        else:
            curr_str = format_bytes(current_bytes)
            spd_str = f"{format_bytes(speed)}/s"
            self.status_label.setText(f"{curr_str} دانلود شده - {spd_str}")

    def on_operation_finished(self, success: bool, message: str, output_folder: str) -> None:
        """Handle completion of operation with dialog offering to open destination folder."""
        self.set_ui_busy(False)
        self.status_label.setText(message)

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("نتیجه عملیات")
        msg_box.setText(message)

        if success:
            msg_box.setIcon(QMessageBox.Information)
            open_btn = msg_box.addButton("نمایش در پوشه", QMessageBox.ActionRole)
            ok_btn = msg_box.addButton("تایید", QMessageBox.AcceptRole)
            msg_box.setDefaultButton(ok_btn)
            msg_box.exec_()

            if msg_box.clickedButton() == open_btn:
                open_in_file_manager(output_folder)
        else:
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.addButton("تایید", QMessageBox.AcceptRole)
            msg_box.exec_()

    def set_ui_busy(self, busy: bool, mode: str = "fetch") -> None:
        """Enable or disable interactive widgets during active tasks."""
        self.link_input.setEnabled(not busy)
        self.fetch_button.setEnabled(not busy)
        self.quality_combo.setEnabled(not busy)
        self.action_combo.setEnabled(not busy)
        self.folder_input.setEnabled(not busy)
        self.browse_button.setEnabled(not busy)
        self.start_button.setEnabled(not busy)

        if busy:
            if mode == "operation":
                self.cancel_button.setEnabled(True)
                self.start_button.setText("در حال انجام عملیات...")
            else:
                self.cancel_button.setEnabled(False)
                self.fetch_button.setText("در حال دریافت...")
        else:
            self.cancel_button.setEnabled(False)
            self.start_button.setText("شروع عملیات")
            self.fetch_button.setText("دریافت اطلاعات لیست / ویدیو")


def main() -> None:
    """Main entry point for GUI application."""
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = ModernApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
