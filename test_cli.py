"""Unit tests for cli.py module of Aparat Downloader."""

import io
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from cli import (
    BANNER,
    build_quality_options,
    format_bytes,
    format_progress_bar,
    format_video_table,
    main,
    parse_cli_args,
    resolve_action_choice,
    resolve_quality_choice,
)


class TestFormatBytes(unittest.TestCase):
    """Tests for format_bytes helper."""

    def test_bytes_formatting(self):
        self.assertEqual(format_bytes(0), "0.0 B")
        self.assertEqual(format_bytes(512), "512.0 B")
        self.assertEqual(format_bytes(1024), "1.0 KB")
        self.assertEqual(format_bytes(1536), "1.5 KB")
        self.assertEqual(format_bytes(1024 * 1024), "1.0 MB")
        self.assertEqual(format_bytes(25 * 1024 * 1024), "25.0 MB")
        self.assertEqual(format_bytes(1024 * 1024 * 1024), "1.0 GB")
        self.assertEqual(format_bytes(2.5 * 1024 * 1024 * 1024), "2.5 GB")


class TestFormatProgressBar(unittest.TestCase):
    """Tests for format_progress_bar helper."""

    def test_progress_bar_known_total(self):
        current = 50 * 1024 * 1024
        total = 100 * 1024 * 1024
        speed = 2.5 * 1024 * 1024
        bar_text = format_progress_bar(
            current_bytes=current,
            total_bytes=total,
            speed_bytes_per_sec=speed,
            current_item=1,
            total_items=3,
            bar_width=20,
        )
        self.assertIn("[Video 1/3]", bar_text)
        self.assertIn("50.0%", bar_text)
        self.assertIn("50.0 MB / 100.0 MB", bar_text)
        self.assertIn("2.5 MB/s", bar_text)
        self.assertIn("██████████░░░░░░░░░░", bar_text)

    def test_progress_bar_single_item_no_prefix(self):
        current = 10 * 1024 * 1024
        total = 10 * 1024 * 1024
        speed = 1.0 * 1024 * 1024
        bar_text = format_progress_bar(
            current_bytes=current,
            total_bytes=total,
            speed_bytes_per_sec=speed,
            current_item=None,
            total_items=None,
            bar_width=10,
        )
        self.assertNotIn("[Video", bar_text)
        self.assertIn("100.0%", bar_text)
        self.assertIn("██████████", bar_text)

    def test_progress_bar_unknown_total(self):
        current = 15 * 1024 * 1024
        total = 0
        speed = 1.2 * 1024 * 1024
        bar_text = format_progress_bar(
            current_bytes=current,
            total_bytes=total,
            speed_bytes_per_sec=speed,
            current_item=2,
            total_items=4,
            bar_width=20,
        )
        self.assertIn("[Video 2/4]", bar_text)
        self.assertIn("--.-%", bar_text)
        self.assertIn("15.0 MB / Unknown", bar_text)
        self.assertIn("1.2 MB/s", bar_text)


class TestFormatVideoTable(unittest.TestCase):
    """Tests for format_video_table helper."""

    def test_video_table_rendering(self):
        videos = [
            {
                "title": "Lesson 1: Introduction",
                "duration_formatted": "10:30",
                "qualities": [
                    {"profile": "360p", "urls": ["http://ex.com/360"]},
                    {"profile": "720p", "urls": ["http://ex.com/720"]},
                    {"profile": "144p", "urls": ["http://ex.com/144"]},
                ],
            },
            {
                "title": "Lesson 2: Advanced Topics",
                "duration_formatted": "25:45",
                "qualities": [
                    {"profile": "480p", "urls": ["http://ex.com/480"]},
                    {"profile": "1080p", "urls": ["http://ex.com/1080"]},
                ],
            },
        ]
        table = format_video_table(videos)
        self.assertIn("#", table)
        self.assertIn("Duration", table)
        self.assertIn("Qualities Available", table)
        self.assertIn("Title", table)
        self.assertIn("Lesson 1: Introduction", table)
        self.assertIn("Lesson 2: Advanced Topics", table)
        self.assertIn("10:30", table)
        self.assertIn("25:45", table)
        # Check ascending order in table: 144p, 360p, 720p
        self.assertIn("144p, 360p, 720p", table)
        self.assertIn("480p, 1080p", table)

    def test_video_table_empty_qualities(self):
        videos = [
            {
                "title": "No qualities video",
                "duration_formatted": "00:00",
                "qualities": [],
            }
        ]
        table = format_video_table(videos)
        self.assertIn("No qualities video", table)
        self.assertIn("-", table)


class TestQualityOptionsAndResolution(unittest.TestCase):
    """Tests for quality selection options and resolving choices."""

    def test_build_quality_options(self):
        qualities = ["1080p", "720p", "480p", "360p"]
        options = build_quality_options(qualities)
        self.assertEqual(len(options), 5)
        self.assertEqual(options[0][0], "1")
        self.assertIn("Best Available", options[0][1])
        self.assertEqual(options[1][0], "2")
        self.assertIn("1080p", options[1][1])
        self.assertIn("fallback", options[1][1])
        self.assertEqual(options[2][0], "3")
        self.assertIn("720p", options[2][1])

    def test_resolve_quality_choice_defaults_and_numbers(self):
        qualities = ["720p", "480p", "360p"]
        # Default empty choice
        self.assertEqual(resolve_quality_choice("", qualities), "best")
        self.assertEqual(resolve_quality_choice("   ", qualities), "best")
        # Choice 1
        self.assertEqual(resolve_quality_choice("1", qualities), "best")
        self.assertEqual(resolve_quality_choice("best", qualities), "best")
        self.assertEqual(resolve_quality_choice("BEST", qualities), "best")
        # Numbered choices
        self.assertEqual(resolve_quality_choice("2", qualities), "720p")
        self.assertEqual(resolve_quality_choice("3", qualities), "480p")
        self.assertEqual(resolve_quality_choice("4", qualities), "360p")

    def test_resolve_quality_choice_by_name(self):
        qualities = ["720p", "480p", "360p"]
        self.assertEqual(resolve_quality_choice("720p", qualities), "720p")
        self.assertEqual(resolve_quality_choice("720", qualities), "720p")
        self.assertEqual(resolve_quality_choice("360", qualities), "360p")

    def test_resolve_quality_choice_invalid(self):
        qualities = ["720p", "480p", "360p"]
        self.assertIsNone(resolve_quality_choice("5", qualities))
        self.assertIsNone(resolve_quality_choice("0", qualities))
        self.assertIsNone(resolve_quality_choice("xyz", qualities))


class TestActionResolution(unittest.TestCase):
    """Tests for resolve_action_choice helper."""

    def test_action_choices(self):
        self.assertEqual(resolve_action_choice(""), "download")
        self.assertEqual(resolve_action_choice("1"), "download")
        self.assertEqual(resolve_action_choice("download"), "download")
        self.assertEqual(resolve_action_choice("d"), "download")
        self.assertEqual(resolve_action_choice("2"), "export")
        self.assertEqual(resolve_action_choice("export"), "export")
        self.assertEqual(resolve_action_choice("txt"), "export")
        self.assertEqual(resolve_action_choice("e"), "export")
        self.assertIsNone(resolve_action_choice("3"))
        self.assertIsNone(resolve_action_choice("foo"))


class TestArgParsing(unittest.TestCase):
    """Tests for parse_cli_args helper."""

    def test_default_empty_args(self):
        args = parse_cli_args([])
        self.assertIsNone(args.url_or_id)
        self.assertIsNone(args.quality)
        self.assertFalse(args.export)
        self.assertIsNone(args.dest)

    def test_full_cli_args(self):
        args = parse_cli_args(
            ["11402450", "--quality", "720", "--export", "--dest", "./output"]
        )
        self.assertEqual(args.url_or_id, "11402450")
        self.assertEqual(args.quality, "720")
        self.assertTrue(args.export)
        self.assertEqual(args.dest, "./output")

    def test_short_flags(self):
        args = parse_cli_args(["nbl9l8o", "-q", "best", "-e", "-d", "/tmp/videos"])
        self.assertEqual(args.url_or_id, "nbl9l8o")
        self.assertEqual(args.quality, "best")
        self.assertTrue(args.export)
        self.assertEqual(args.dest, "/tmp/videos")


class TestCLIFlows(unittest.TestCase):
    """Tests for high-level main() CLI execution flows."""

    def setUp(self):
        self.sample_target_playlist = {
            "type": "playlist",
            "id": "11402450",
            "title": "Python Tutorials",
            "channel_name": "Dev Channel",
            "videos": [
                {
                    "uid": "vid1",
                    "title": "Video 1",
                    "duration": 120,
                    "duration_formatted": "02:00",
                    "qualities": [{"profile": "720p", "urls": ["http://ex.com/vid1.mp4"]}],
                    "poster": "",
                },
                {
                    "uid": "vid2",
                    "title": "Video 2",
                    "duration": 180,
                    "duration_formatted": "03:00",
                    "qualities": [{"profile": "720p", "urls": ["http://ex.com/vid2.mp4"]}],
                    "poster": "",
                },
            ],
        }

    @patch("cli.AparatClient")
    def test_automated_export_flow(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.fetch_target.return_value = self.sample_target_playlist
        mock_client.fetch_all_video_qualities.return_value = self.sample_target_playlist["videos"]
        mock_client.get_available_qualities.return_value = ["720p"]
        mock_client.export_links_to_txt.return_value = 2

        with tempfile.TemporaryDirectory() as tmpdir:
            out_buf = io.StringIO()
            with patch("sys.stdout", out_buf):
                exit_code = main(
                    ["11402450", "--quality", "720", "--export", "--dest", tmpdir]
                )

            self.assertEqual(exit_code, 0)
            mock_client.fetch_target.assert_called_once_with("11402450", "playlist")
            mock_client.export_links_to_txt.assert_called_once()
            output = out_buf.getvalue()
            self.assertIn("Python Tutorials", output)
            self.assertIn("Exported", output)

    @patch("cli.AparatClient")
    def test_automated_download_flow(self, mock_client_cls):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.fetch_target.return_value = self.sample_target_playlist
        mock_client.fetch_all_video_qualities.return_value = self.sample_target_playlist["videos"]
        mock_client.get_available_qualities.return_value = ["720p"]
        mock_client.resolve_download_link.return_value = ("http://ex.com/vid.mp4", "720p", False)
        mock_client.download_video.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            out_buf = io.StringIO()
            with patch("sys.stdout", out_buf):
                exit_code = main(
                    ["11402450", "--quality", "720", "--dest", tmpdir]
                )

            self.assertEqual(exit_code, 0)
            self.assertEqual(mock_client.download_video.call_count, 2)

    @patch("cli.input")
    @patch("cli.AparatClient")
    def test_interactive_quit(self, mock_client_cls, mock_input):
        mock_input.side_effect = ["q"]
        out_buf = io.StringIO()
        with patch("sys.stdout", out_buf):
            exit_code = main([])
        self.assertEqual(exit_code, 0)
        self.assertIn("Exiting", out_buf.getvalue())

    @patch("cli.input")
    @patch("cli.AparatClient")
    def test_interactive_invalid_then_valid(self, mock_client_cls, mock_input):
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.fetch_target.return_value = self.sample_target_playlist
        mock_client.fetch_all_video_qualities.return_value = self.sample_target_playlist["videos"]
        mock_client.get_available_qualities.return_value = ["720p"]
        mock_client.export_links_to_txt.return_value = 2

        with tempfile.TemporaryDirectory() as tmpdir:
            # Inputs:
            # 1. Invalid URL "https://google.com"
            # 2. Valid URL "11402450"
            # 3. Quality selection: "1" (Best)
            # 4. Action selection: "2" (Export)
            # 5. Dest path: tmpdir
            mock_input.side_effect = [
                "https://google.com",
                "11402450",
                "1",
                "2",
                tmpdir,
            ]
            out_buf = io.StringIO()
            with patch("sys.stdout", out_buf):
                exit_code = main([])

            self.assertEqual(exit_code, 0)
            output = out_buf.getvalue()
            self.assertIn("Invalid Aparat URL or ID", output)
            self.assertIn("Python Tutorials", output)


if __name__ == "__main__":
    unittest.main()
