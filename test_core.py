"""Unit tests for core.py module of Aparat Downloader."""

import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from core import (
    AparatClient,
    AparatDownloader,
    CancellationToken,
    format_duration,
    get_available_qualities,
    parse_aparat_input,
    resolve_download_link,
    sanitize_filename,
)


class TestParseAparatInput(unittest.TestCase):
    """Tests for parse_aparat_input."""

    def test_raw_playlist_id(self):
        target_type, identifier = parse_aparat_input("11402450")
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_playlist_url_trailing_slash(self):
        target_type, identifier = parse_aparat_input(
            "https://www.aparat.com/playlist/11402450/"
        )
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_playlist_url_no_trailing_slash(self):
        target_type, identifier = parse_aparat_input(
            "https://www.aparat.com/playlist/11402450"
        )
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_playlist_url_with_query_params(self):
        target_type, identifier = parse_aparat_input(
            "https://www.aparat.com/playlist/11402450?utm_source=test"
        )
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_video_url_no_trailing_slash(self):
        target_type, identifier = parse_aparat_input("https://www.aparat.com/v/nbl9l8o")
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_video_url_trailing_slash(self):
        target_type, identifier = parse_aparat_input("https://www.aparat.com/v/nbl9l8o/")
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_raw_video_hash(self):
        target_type, identifier = parse_aparat_input("nbl9l8o")
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_video_url_with_query_params(self):
        target_type, identifier = parse_aparat_input(
            "https://www.aparat.com/v/nbl9l8o?playlist=11402450"
        )
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_whitespace_handling(self):
        target_type, identifier = parse_aparat_input("  11402450  \n")
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_schemeless_playlist_url(self):
        target_type, identifier = parse_aparat_input("aparat.com/playlist/11402450")
        self.assertEqual(target_type, "playlist")
        self.assertEqual(identifier, "11402450")

    def test_schemeless_video_url(self):
        target_type, identifier = parse_aparat_input("www.aparat.com/v/nbl9l8o")
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_schemeless_video_url_trailing_slash(self):
        target_type, identifier = parse_aparat_input("aparat.com/v/nbl9l8o/")
        self.assertEqual(target_type, "video")
        self.assertEqual(identifier, "nbl9l8o")

    def test_invalid_input(self):
        with self.assertRaises(ValueError):
            parse_aparat_input("")

        with self.assertRaises(ValueError):
            parse_aparat_input("   ")

        with self.assertRaises(ValueError):
            parse_aparat_input("https://google.com/search")


class TestSanitizeFilename(unittest.TestCase):
    """Tests for sanitize_filename."""

    def test_removes_illegal_characters(self):
        raw = 'Episode / 01 : "Pilot" * <Special> ? | Test \\ File'
        cleaned = sanitize_filename(raw)
        for char in r'\/:*?"<>|':
            self.assertNotIn(char, cleaned)

    def test_unescapes_html_entities(self):
        raw = 'Ninja Turtles &quot;2024&quot; &amp; Friends'
        cleaned = sanitize_filename(raw)
        self.assertNotIn("&quot;", cleaned)
        self.assertNotIn('"', cleaned)
        self.assertIn("2024", cleaned)
        self.assertIn("&", cleaned)

    def test_strips_leading_trailing_dots_and_spaces(self):
        raw = "  ...My Video Title...   "
        cleaned = sanitize_filename(raw)
        self.assertEqual(cleaned, "My Video Title")

    def test_empty_fallback(self):
        raw = "??::***"
        cleaned = sanitize_filename(raw)
        self.assertEqual(cleaned, "untitled")


class TestFormatDuration(unittest.TestCase):
    """Tests for format_duration."""

    def test_seconds_only(self):
        self.assertEqual(format_duration(45), "00:45")

    def test_minutes_and_seconds(self):
        self.assertEqual(format_duration(1304), "21:44")

    def test_hours_minutes_seconds(self):
        self.assertEqual(format_duration(3665), "01:01:05")

    def test_zero_or_none(self):
        self.assertEqual(format_duration(0), "00:00")
        self.assertEqual(format_duration(None), "00:00")


class TestResolveDownloadLink(unittest.TestCase):
    """Tests for resolve_download_link and fallback quality selection."""

    def setUp(self):
        self.video = {
            "uid": "nbl9l8o",
            "title": "Ninja Turtles Ep 1",
            "qualities": [
                {"profile": "144p", "urls": ["https://cdn.aparat.com/144.mp4"]},
                {"profile": "240p", "urls": ["https://cdn.aparat.com/240.mp4"]},
                {"profile": "360p", "urls": ["https://cdn.aparat.com/360.mp4"]},
                {"profile": "720p", "urls": ["https://cdn.aparat.com/720.mp4"]},
            ],
        }

    def test_exact_match(self):
        url, profile, is_fallback = resolve_download_link(self.video, "720p")
        self.assertEqual(url, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile, "720p")
        self.assertFalse(is_fallback)

    def test_exact_match_without_p_suffix(self):
        url, profile, is_fallback = resolve_download_link(self.video, "720")
        self.assertEqual(url, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile, "720p")
        self.assertFalse(is_fallback)

    def test_fallback_when_quality_unavailable(self):
        url, profile, is_fallback = resolve_download_link(self.video, "1080p")
        # Highest available is 720p
        self.assertEqual(url, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile, "720p")
        self.assertTrue(is_fallback)

    def test_best_selection(self):
        url, profile, is_fallback = resolve_download_link(self.video, "best")
        self.assertEqual(url, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile, "720p")
        self.assertFalse(is_fallback)

    def test_empty_or_none_defaults_to_best(self):
        url1, profile1, is_fallback1 = resolve_download_link(self.video, "")
        url2, profile2, is_fallback2 = resolve_download_link(self.video, None)
        self.assertEqual(url1, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile1, "720p")
        self.assertFalse(is_fallback1)
        self.assertEqual(url2, "https://cdn.aparat.com/720.mp4")
        self.assertEqual(profile2, "720p")
        self.assertFalse(is_fallback2)

    def test_client_method_delegation(self):
        client = AparatClient()
        url, profile, is_fallback = client.resolve_download_link(self.video, "360p")
        self.assertEqual(url, "https://cdn.aparat.com/360.mp4")
        self.assertEqual(profile, "360p")
        self.assertFalse(is_fallback)

    def test_no_qualities_raises(self):
        with self.assertRaises(ValueError):
            resolve_download_link({"uid": "empty", "qualities": []}, "720p")

    def test_empty_urls_raises(self):
        with self.assertRaises(ValueError):
            resolve_download_link(
                {"uid": "empty_urls", "qualities": [{"profile": "720p", "urls": []}]},
                "720p",
            )


class TestGetAvailableQualities(unittest.TestCase):
    """Tests for get_available_qualities."""

    def test_unique_and_sorted_descending(self):
        videos = [
            {
                "uid": "v1",
                "qualities": [
                    {"profile": "360p", "urls": ["u1"]},
                    {"profile": "144p", "urls": ["u2"]},
                ],
            },
            {
                "uid": "v2",
                "qualities": [
                    {"profile": "1080p", "urls": ["u3"]},
                    {"profile": "720p", "urls": ["u4"]},
                    {"profile": "360p", "urls": ["u5"]},
                ],
            },
            {
                "uid": "v3",
                "qualities": [
                    {"profile": "480p", "urls": ["u6"]},
                    {"profile": "240p", "urls": ["u7"]},
                ],
            },
        ]
        qualities = get_available_qualities(videos)
        self.assertEqual(
            qualities, ["1080p", "720p", "480p", "360p", "240p", "144p"]
        )

    def test_empty_videos_list(self):
        self.assertEqual(get_available_qualities([]), [])


class TestExportLinksToTxt(unittest.TestCase):
    """Tests for export_links_to_txt."""

    def test_export_links_file_creation(self):
        client = AparatClient()
        videos = [
            {
                "uid": "v1",
                "title": "Episode 1",
                "qualities": [
                    {"profile": "720p", "urls": ["https://cdn.aparat.com/ep1-720.mp4"]},
                ],
            },
            {
                "uid": "v2",
                "title": "Episode 2",
                "qualities": [
                    {"profile": "480p", "urls": ["https://cdn.aparat.com/ep2-480.mp4"]},
                ],
            },
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            output_file = os.path.join(tmpdir, "links.txt")
            count = client.export_links_to_txt(videos, "720p", output_file)
            self.assertEqual(count, 2)
            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("https://cdn.aparat.com/ep1-720.mp4", content)
            self.assertIn("https://cdn.aparat.com/ep2-480.mp4", content)
            self.assertIn("# Episode 1 - 720p", content)
            self.assertIn("# Episode 2 - 480p", content)


class TestCancellationToken(unittest.TestCase):
    """Tests for CancellationToken."""

    def test_cancellation(self):
        token = CancellationToken()
        self.assertFalse(token.is_cancelled())
        token.cancel()
        self.assertTrue(token.is_cancelled())


class TestAparatDownloaderBackwardsCompatibility(unittest.TestCase):
    """Tests ensuring legacy AparatDownloader class interface works."""

    def test_initialization(self):
        downloader = AparatDownloader(
            playlist_id="11402450",
            quality="720",
            for_download_manager=True,
            destination_path="test_downloads",
        )
        self.assertEqual(downloader.playlist_id, "11402450")
        self.assertEqual(downloader.quality, "720")
        self.assertTrue(downloader.for_download_manager)
        self.assertEqual(downloader.destination_path, "test_downloads")
        # Clean up test_downloads folder created by legacy __init__
        if os.path.exists("test_downloads"):
            os.rmdir("test_downloads")


class TestAparatClientFetch(unittest.TestCase):
    """Tests for AparatClient fetch methods using mocked responses."""

    @patch("requests.Session.get")
    def test_fetch_playlist_single_page(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "attributes": {
                    "title": "My &quot;Test&quot; Playlist",
                    "channel_name": "Channel One",
                }
            },
            "included": [
                {
                    "type": "Video",
                    "attributes": {
                        "uid": "vid1",
                        "title": "Video 1",
                        "duration": 120,
                        "big_poster": "https://poster1.jpg",
                    },
                },
                {
                    "type": "Video",
                    "attributes": {
                        "uid": "vid2",
                        "title": "Video 2",
                        "duration": 240,
                        "big_poster": "https://poster2.jpg",
                    },
                },
                {"type": "channel", "attributes": {"name": "Channel One"}},
            ],
        }
        mock_get.return_value = mock_resp

        client = AparatClient()
        target = client.fetch_target("12345", "playlist")

        self.assertEqual(target["type"], "playlist")
        self.assertEqual(target["id"], "12345")
        self.assertEqual(target["title"], 'My "Test" Playlist')
        self.assertEqual(target["channel_name"], "Channel One")
        self.assertEqual(len(target["videos"]), 2)
        self.assertEqual(target["videos"][0]["uid"], "vid1")
        self.assertEqual(target["videos"][0]["duration_formatted"], "02:00")
        self.assertEqual(target["videos"][1]["duration_formatted"], "04:00")

    @patch("requests.Session.get")
    def test_fetch_playlist_pagination(self, mock_get):
        mock_resp1 = MagicMock()
        mock_resp1.status_code = 200
        mock_resp1.json.return_value = {
            "data": {"attributes": {"title": "Paginated Playlist"}},
            "links": {"next": "https://www.aparat.com/page2"},
            "included": [
                {"type": "Video", "attributes": {"uid": "vid1", "title": "Video 1"}}
            ],
        }
        mock_resp2 = MagicMock()
        mock_resp2.status_code = 200
        mock_resp2.json.return_value = {
            "data": {"attributes": {"title": "Paginated Playlist"}},
            "links": {},
            "included": [
                {"type": "Video", "attributes": {"uid": "vid2", "title": "Video 2"}}
            ],
        }
        mock_get.side_effect = [mock_resp1, mock_resp2]

        client = AparatClient()
        target = client.fetch_target("999", "playlist")

        self.assertEqual(len(target["videos"]), 2)
        self.assertEqual(target["videos"][0]["uid"], "vid1")
        self.assertEqual(target["videos"][1]["uid"], "vid2")

    @patch("requests.Session.get")
    def test_fetch_single_video(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "attributes": {
                    "uid": "single1",
                    "title": "Single &amp; Video",
                    "duration": 3661,
                    "file_link_all": [
                        {"profile": "720p", "urls": ["https://cdn.test/720.mp4"]}
                    ],
                }
            },
            "included": [{"type": "channel", "attributes": {"name": "Creator Alpha"}}],
        }
        mock_get.return_value = mock_resp

        client = AparatClient()
        target = client.fetch_target("single1", "video")

        self.assertEqual(target["type"], "video")
        self.assertEqual(target["id"], "single1")
        self.assertEqual(target["title"], "Single & Video")
        self.assertEqual(target["channel_name"], "Creator Alpha")
        self.assertEqual(len(target["videos"]), 1)
        self.assertEqual(target["videos"][0]["duration_formatted"], "01:01:01")
        self.assertEqual(target["videos"][0]["qualities"][0]["profile"], "720p")

    def test_invalid_target_type(self):
        client = AparatClient()
        with self.assertRaises(ValueError):
            client.fetch_target("123", "invalid_type")

    @patch("requests.Session.get")
    def test_fetch_all_video_qualities(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "data": {
                "attributes": {
                    "file_link_all": [
                        {"profile": "480p", "urls": ["https://cdn.test/480.mp4"]}
                    ]
                }
            }
        }
        mock_get.return_value = mock_resp

        client = AparatClient()
        videos = [
            {"uid": "v1", "title": "V1", "qualities": []},
            {"uid": "v2", "title": "V2", "qualities": []},
        ]

        progress_calls = []

        def on_progress(done, total):
            progress_calls.append((done, total))

        result = client.fetch_all_video_qualities(
            videos, max_workers=2, progress_cb=on_progress
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["qualities"][0]["profile"], "480p")
        self.assertEqual(result[1]["qualities"][0]["profile"], "480p")
        self.assertIn((2, 2), progress_calls)


class TestAparatClientDownload(unittest.TestCase):
    """Tests for AparatClient download_video streaming and cancellation."""

    @patch("requests.Session.get")
    def test_download_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "12"}
        mock_resp.iter_content.return_value = [b"chunk1", b"chunk2"]
        mock_get.return_value = mock_resp

        client = AparatClient()
        progress_calls = []

        def on_progress(downloaded, total, speed):
            progress_calls.append((downloaded, total))

        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, "video.mp4")
            success = client.download_video(
                "https://test.com/v.mp4", dest, progress_callback=on_progress
            )
            self.assertTrue(success)
            self.assertTrue(os.path.exists(dest))
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"chunk1chunk2")

        self.assertTrue(len(progress_calls) > 0)
        self.assertEqual(progress_calls[-1], (12, 12))

    @patch("requests.Session.get")
    def test_download_cancellation(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "100"}

        token = CancellationToken()

        def chunk_gen():
            yield b"first_chunk"
            token.cancel()
            yield b"second_chunk"

        mock_resp.iter_content.return_value = chunk_gen()
        mock_get.return_value = mock_resp

        client = AparatClient()
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, "cancel.mp4")
            success = client.download_video(
                "https://test.com/v.mp4", dest, cancel_token=token
            )
            self.assertFalse(success)

    @patch("requests.Session.get")
    def test_download_non_numeric_content_length(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.headers = {"content-length": "not-a-number"}
        mock_resp.iter_content.return_value = [b"stream_data"]
        mock_get.return_value = mock_resp

        client = AparatClient()
        with tempfile.TemporaryDirectory() as tmpdir:
            dest = os.path.join(tmpdir, "no_cl.mp4")
            success = client.download_video("https://test.com/v.mp4", dest)
            self.assertTrue(success)
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"stream_data")


class TestAparatDownloaderResilience(unittest.TestCase):
    """Tests ensuring AparatDownloader is resilient to individual video failures."""

    @patch.object(AparatClient, "download_video")
    @patch.object(AparatClient, "fetch_all_video_qualities")
    @patch.object(AparatClient, "fetch_target")
    def test_download_playlist_resilient_to_single_video_failure(
        self, mock_fetch_target, mock_fetch_quals, mock_download
    ):
        mock_fetch_target.return_value = {
            "title": "Playlist Resilience",
            "videos": [
                {
                    "uid": "v1",
                    "title": "Broken Video",
                    "qualities": [],  # will raise ValueError on resolve_download_link
                },
                {
                    "uid": "v2",
                    "title": "Good Video",
                    "qualities": [{"profile": "720p", "urls": ["https://cdn/v2.mp4"]}],
                },
            ],
        }
        mock_download.return_value = True

        with tempfile.TemporaryDirectory() as tmpdir:
            downloader = AparatDownloader(
                playlist_id="12345", quality="720p", destination_path=tmpdir
            )
            # Should NOT raise an exception despite the first video failing
            downloader.download_playlist()
            self.assertEqual(mock_download.call_count, 1)


if __name__ == "__main__":
    unittest.main()
