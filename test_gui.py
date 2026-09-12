"""Headless unit and smoke tests for modern PyQt5 GUI (gui.py).

Runs offscreen using os.environ["QT_QPA_PLATFORM"] = "offscreen" to support
CI, virtualized, and headless development environments.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# Ensure Qt runs offscreen without display server
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

# Initialize a single QApplication instance for all tests
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

import gui
from gui import (
    FetchTargetWorker,
    OperationWorker,
    ModernApp,
    format_bytes,
)
from core import CancellationToken


class TestFormatBytes(unittest.TestCase):
    """Test byte and speed string formatting."""

    def test_bytes_formatting(self):
        self.assertEqual(format_bytes(500), "500.0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1024 * 1024 * 5.5), "5.5 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024 * 2.3), "2.3 GB")


class TestFetchTargetWorker(unittest.TestCase):
    """Test background metadata fetching worker."""

    def test_worker_signals_and_init(self):
        worker = FetchTargetWorker("11402450")
        self.assertEqual(worker.target_input, "11402450")
        self.assertTrue(hasattr(worker, "progress"))
        self.assertTrue(hasattr(worker, "finished"))
        self.assertTrue(hasattr(worker, "error"))

    def test_worker_empty_input_error(self):
        worker = FetchTargetWorker("")
        errors = []
        worker.error.connect(errors.append)
        worker.run()
        self.assertEqual(len(errors), 1)
        self.assertIn("شناسه", errors[0])

    def test_worker_success(self):
        mock_client = MagicMock()
        mock_data = {
            "type": "playlist",
            "id": "11402450",
            "title": "آموزش پایتون",
            "channel_name": "کانال آموزشی",
            "videos": [
                {
                    "uid": "v1",
                    "title": "قسمت اول",
                    "duration": 120,
                    "duration_formatted": "02:00",
                    "qualities": [{"profile": "720p", "urls": ["http://test/720.mp4"]}],
                },
                {
                    "uid": "v2",
                    "title": "قسمت دوم",
                    "duration": 240,
                    "duration_formatted": "04:00",
                    "qualities": [{"profile": "1080p", "urls": ["http://test/1080.mp4"]}],
                },
            ],
        }
        mock_client.fetch_target.return_value = mock_data

        def mock_fetch_qualities(videos, max_workers=5, progress_cb=None):
            if progress_cb:
                progress_cb(1, 2)
                progress_cb(2, 2)
            return videos

        mock_client.fetch_all_video_qualities.side_effect = mock_fetch_qualities

        worker = FetchTargetWorker("11402450", client=mock_client)
        progress_events = []
        finished_results = []
        worker.progress.connect(lambda c, t: progress_events.append((c, t)))
        worker.finished.connect(finished_results.append)

        worker.run()

        self.assertEqual(len(finished_results), 1)
        self.assertEqual(finished_results[0]["title"], "آموزش پایتون")
        self.assertEqual(len(finished_results[0]["videos"]), 2)
        self.assertEqual(progress_events, [(1, 2), (2, 2)])

    def test_worker_network_error(self):
        mock_client = MagicMock()
        mock_client.fetch_target.side_effect = ConnectionError("Failed to connect")

        worker = FetchTargetWorker("11402450", client=mock_client)
        errors = []
        worker.error.connect(errors.append)

        worker.run()

        self.assertEqual(len(errors), 1)
        self.assertIn("Failed to connect", errors[0])


class TestOperationWorker(unittest.TestCase):
    """Test background operation worker for download and export."""

    def setUp(self):
        self.sample_videos = [
            {
                "uid": "vid1",
                "title": "جلسه اول",
                "duration": 60,
                "duration_formatted": "01:00",
                "qualities": [
                    {"profile": "720p", "urls": ["http://cdn/v1_720.mp4"]},
                    {"profile": "480p", "urls": ["http://cdn/v1_480.mp4"]},
                ],
            },
            {
                "uid": "vid2",
                "title": "جلسه دوم",
                "duration": 120,
                "duration_formatted": "02:00",
                "qualities": [
                    {"profile": "720p", "urls": ["http://cdn/v2_720.mp4"]},
                ],
            },
        ]
        self.sample_target = {
            "type": "playlist",
            "id": "11402450",
            "title": "دوره پایتون",
            "videos": self.sample_videos,
        }

    def test_export_action_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            worker = OperationWorker(
                videos=self.sample_videos,
                preferred_quality="720p",
                target_data=self.sample_target,
                destination_path=tmpdir,
                action="export",
            )
            finished_results = []
            worker.finished.connect(lambda s, m, p: finished_results.append((s, m, p)))

            worker.run()

            self.assertEqual(len(finished_results), 1)
            success, msg, path = finished_results[0]
            self.assertTrue(success)
            self.assertIn("لینک", msg)
            self.assertEqual(path, tmpdir)

            expected_file = os.path.join(tmpdir, "دوره پایتون.txt")
            self.assertTrue(os.path.exists(expected_file))
            with open(expected_file, "r", encoding="utf-8") as f:
                content = f.read()
                self.assertIn("http://cdn/v1_720.mp4", content)
                self.assertIn("http://cdn/v2_720.mp4", content)

    def test_download_action_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mock_client = MagicMock()
            mock_client.resolve_download_link.side_effect = [
                ("http://cdn/v1_720.mp4", "720p", False),
                ("http://cdn/v2_720.mp4", "720p", False),
            ]

            def mock_download(url, filepath, progress_callback=None, cancel_token=None):
                if progress_callback:
                    progress_callback(500, 1000, 250.0)
                    progress_callback(1000, 1000, 500.0)
                return True

            mock_client.download_video.side_effect = mock_download

            worker = OperationWorker(
                videos=self.sample_videos,
                preferred_quality="720p",
                target_data=self.sample_target,
                destination_path=tmpdir,
                action="download",
                client=mock_client,
            )

            overall_events = []
            file_events = []
            finished_results = []
            worker.overall_progress.connect(
                lambda idx, tot, title: overall_events.append((idx, tot, title))
            )
            worker.file_progress.connect(
                lambda cur, tot, spd: file_events.append((cur, tot, spd))
            )
            worker.finished.connect(
                lambda s, m, p: finished_results.append((s, m, p))
            )

            worker.run()

            self.assertEqual(len(finished_results), 1)
            success, msg, path = finished_results[0]
            self.assertTrue(success)
            self.assertEqual(len(overall_events), 2)
            self.assertEqual(overall_events[0][0], 1)
            self.assertEqual(overall_events[1][0], 2)
            self.assertGreaterEqual(len(file_events), 2)

    def test_cancellation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            cancel_token = CancellationToken()
            cancel_token.cancel()

            worker = OperationWorker(
                videos=self.sample_videos,
                preferred_quality="720p",
                target_data=self.sample_target,
                destination_path=tmpdir,
                action="download",
                cancel_token=cancel_token,
            )
            finished_results = []
            worker.finished.connect(
                lambda s, m, p: finished_results.append((s, m, p))
            )

            worker.run()

            self.assertEqual(len(finished_results), 1)
            success, msg, path = finished_results[0]
            self.assertFalse(success)
            self.assertIn("متوقف", msg)


class TestModernAppHeadless(unittest.TestCase):
    """Test ModernApp GUI widget instantiation, RTL layout, and signals."""

    def setUp(self):
        self.window = ModernApp()

    def tearDown(self):
        self.window.close()

    def test_window_properties(self):
        self.assertIn("آپارات", self.window.windowTitle())
        self.assertIn("علی بختیاری", self.window.windowTitle())
        self.assertEqual(self.window.layoutDirection(), Qt.RightToLeft)

    def test_required_widgets_exist(self):
        # Input section
        self.assertTrue(hasattr(self.window, "link_input"))
        self.assertTrue(hasattr(self.window, "fetch_button"))

        # Summary labels
        self.assertTrue(hasattr(self.window, "summary_title_label"))
        self.assertTrue(hasattr(self.window, "summary_channel_label"))
        self.assertTrue(hasattr(self.window, "summary_type_label"))
        self.assertTrue(hasattr(self.window, "summary_count_label"))

        # Video Table
        self.assertTrue(hasattr(self.window, "video_table"))
        self.assertEqual(self.window.video_table.columnCount(), 4)
        headers = [
            self.window.video_table.horizontalHeaderItem(i).text()
            for i in range(4)
        ]
        self.assertIn("ردیف", headers[0])
        self.assertIn("عنوان", headers[1])
        self.assertIn("مدت زمان", headers[2])
        self.assertIn("کیفیت", headers[3])

        # Options section
        self.assertTrue(hasattr(self.window, "quality_combo"))
        self.assertTrue(hasattr(self.window, "action_combo"))
        self.assertTrue(hasattr(self.window, "folder_input"))
        self.assertTrue(hasattr(self.window, "browse_button"))

        # Action and Progress section
        self.assertTrue(hasattr(self.window, "start_button"))
        self.assertTrue(hasattr(self.window, "cancel_button"))
        self.assertTrue(hasattr(self.window, "overall_progress_bar"))
        self.assertTrue(hasattr(self.window, "file_progress_bar"))
        self.assertTrue(hasattr(self.window, "status_label"))

    def test_populate_summary_and_table_on_fetch(self):
        sample_data = {
            "type": "playlist",
            "id": "11402450",
            "title": "دوره جامع پایتون",
            "channel_name": "آکادمی کد",
            "videos": [
                {
                    "uid": "abc1",
                    "title": "مقدمه و نصب",
                    "duration": 300,
                    "duration_formatted": "05:00",
                    "qualities": [
                        {"profile": "1080p", "urls": ["http://test/1080"]},
                        {"profile": "720p", "urls": ["http://test/720"]},
                    ],
                },
                {
                    "uid": "abc2",
                    "title": "متغیرها و انواع داده",
                    "duration": 650,
                    "duration_formatted": "10:50",
                    "qualities": [
                        {"profile": "720p", "urls": ["http://test/720"]},
                        {"profile": "480p", "urls": ["http://test/480"]},
                    ],
                },
            ],
        }

        self.window.on_fetch_finished(sample_data)

        self.assertIn("دوره جامع پایتون", self.window.summary_title_label.text())
        self.assertIn("آکادمی کد", self.window.summary_channel_label.text())
        self.assertIn("لیست پخش", self.window.summary_type_label.text())
        self.assertIn("2", self.window.summary_count_label.text())

        # Table rows
        self.assertEqual(self.window.video_table.rowCount(), 2)
        self.assertEqual(self.window.video_table.item(0, 1).text(), "مقدمه و نصب")
        self.assertEqual(self.window.video_table.item(0, 2).text(), "05:00")
        self.assertIn("1080p", self.window.video_table.item(0, 3).text())

        self.assertEqual(self.window.video_table.item(1, 1).text(), "متغیرها و انواع داده")
        self.assertEqual(self.window.video_table.item(1, 2).text(), "10:50")

        # Dynamic quality combo population
        combo_items = [
            self.window.quality_combo.itemText(i)
            for i in range(self.window.quality_combo.count())
        ]
        self.assertTrue(any("بهترین" in item for item in combo_items))
        self.assertIn("1080p", combo_items)
        self.assertIn("720p", combo_items)
        self.assertIn("480p", combo_items)

    def test_progress_updates(self):
        self.window.overall_progress_bar.setMaximum(10)
        self.window.on_overall_progress(3, 10, "قسمت سوم")
        self.assertEqual(self.window.overall_progress_bar.value(), 3)
        self.assertIn("قسمت سوم", self.window.status_label.text())

        self.window.on_file_progress(500, 1000, 250000.0)
        self.assertEqual(self.window.file_progress_bar.value(), 50)
        self.assertIn("50%", self.window.status_label.text())

    def test_start_operation_validation_empty_target(self):
        with patch.object(gui.QMessageBox, "warning") as mock_warn:
            self.window.target_data = None
            self.window.start_operation()
            mock_warn.assert_called_once()

    def test_fetch_target_info_empty_input(self):
        self.window.link_input.setText("")
        with patch.object(gui.QMessageBox, "warning") as mock_warn:
            self.window.fetch_target_info()
            mock_warn.assert_called_once()

    def test_on_fetch_error(self):
        with patch.object(gui.QMessageBox, "warning") as mock_warn:
            self.window.on_fetch_error("ارتباط برقرار نشد")
            mock_warn.assert_called_once()
            self.assertIn("خطا", self.window.status_label.text())

    def test_cancel_operation(self):
        self.window.cancel_token = CancellationToken()
        self.window.cancel_button.setEnabled(True)
        self.window.cancel_operation()
        self.assertTrue(self.window.cancel_token.is_cancelled())
        self.assertFalse(self.window.cancel_button.isEnabled())
        self.assertIn("متوقف", self.window.status_label.text())

    def test_on_operation_finished_success(self):
        with patch.object(gui.QMessageBox, "exec_") as mock_exec, \
             patch("gui.open_in_file_manager") as mock_open:
            # Simulate QMessageBox where user does not click open
            self.window.on_operation_finished(True, "دانلود کامل شد", "/fake/path")
            mock_exec.assert_called_once()
            self.assertEqual(self.window.status_label.text(), "دانلود کامل شد")

    def test_on_operation_finished_failure(self):
        with patch.object(gui.QMessageBox, "exec_") as mock_exec:
            self.window.on_operation_finished(False, "خطا رخ داد", "/fake/path")
            mock_exec.assert_called_once()
            self.assertEqual(self.window.status_label.text(), "خطا رخ داد")

    def test_browse_folder(self):
        with patch("PyQt5.QtWidgets.QFileDialog.getExistingDirectory", return_value="/selected/path"):
            self.window.browse_folder()
            self.assertEqual(self.window.folder_input.text(), "/selected/path")

    def test_open_in_file_manager(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("platform.system", return_value="Windows"), \
                 patch("os.startfile", create=True) as mock_startfile:
                gui.open_in_file_manager(tmpdir)
                mock_startfile.assert_called_once_with(tmpdir)


if __name__ == "__main__":
    unittest.main()

