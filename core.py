"""Core engine for Aparat Playlist & Video Downloader v1.0.0.

Provides input parsing, metadata fetching, concurrent quality resolution,
smart quality selection with fallback, streaming downloads with progress callbacks,
and link export for external download managers.
"""

from __future__ import annotations

__version__ = "1.0.0"

import concurrent.futures
import html
import logging
import os
import re
import time
import urllib.parse
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import requests

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
CHUNK_SIZE = 65536  # 64 KB chunks for streaming download


class CancellationToken:
    """Thread-safe cancellation token for cooperative task cancellation."""

    def __init__(self) -> None:
        self._cancelled = False

    def cancel(self) -> None:
        """Signal cancellation."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Check if cancellation has been requested."""
        return self._cancelled


def sanitize_filename(name: str) -> str:
    """Remove illegal filesystem characters and unescape HTML entities.

    Illegal characters removed: \\ / : * ? " < > |
    Strips leading/trailing dots and whitespace.
    Falls back to 'untitled' if the resulting name is empty.
    """
    if not name:
        return "untitled"

    # Unescape HTML entities like &quot;, &amp;, &#39;, etc.
    cleaned = html.unescape(name)

    # Remove Windows & POSIX illegal filename characters
    cleaned = re.sub(r'[\\/:*?"<>|]', "", cleaned)

    # Remove non-printable control characters
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)

    # Strip leading/trailing dots and whitespace
    cleaned = cleaned.strip(" .")

    return cleaned if cleaned else "untitled"


def format_duration(seconds: Optional[Union[int, float, str]]) -> str:
    """Format duration in seconds into HH:MM:SS or MM:SS."""
    if not seconds:
        return "00:00"

    try:
        total_seconds = int(float(seconds))
    except (ValueError, TypeError):
        return "00:00"

    if total_seconds <= 0:
        return "00:00"

    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def parse_aparat_input(input_str: str) -> Tuple[str, str]:
    """Parse user input into (target_type, identifier).

    Target types:
      - 'playlist': identifier is a numeric playlist ID (e.g. '11402450')
      - 'video': identifier is an alphanumeric video hash (e.g. 'nbl9l8o')

    Supports:
      - Raw playlist ID: '11402450'
      - Playlist URL: 'https://www.aparat.com/playlist/11402450/'
      - Video URL: 'https://www.aparat.com/v/nbl9l8o'
      - Raw video hash: 'nbl9l8o'

    Raises ValueError for invalid, empty, or non-Aparat URLs.
    """
    if not input_str or not input_str.strip():
        raise ValueError("Input cannot be empty.")

    cleaned = input_str.strip()
    if "aparat.com" in cleaned.lower() and "://" not in cleaned:
        cleaned = f"https://{cleaned}"
    parsed = urllib.parse.urlparse(cleaned)

    # If it has a URL scheme or netloc
    if parsed.scheme or parsed.netloc:
        netloc = parsed.netloc.lower()
        if "aparat.com" not in netloc:
            raise ValueError(f"Not a valid Aparat URL: {input_str}")

        path = parsed.path

        # Check for video URL pattern first (/v/{hash})
        video_match = re.search(r"/v/([a-zA-Z0-9_-]+)", path)
        if video_match:
            return "video", video_match.group(1)

        # Check for playlist URL pattern (/playlist/{id})
        playlist_match = re.search(r"/playlist/([a-zA-Z0-9_-]+)", path)
        if playlist_match:
            return "playlist", playlist_match.group(1)

        raise ValueError(f"Unrecognized Aparat URL path: {path}")

    # Not a full URL: check raw identifier patterns
    # Aparat playlist IDs are numeric digits
    if cleaned.isdigit():
        return "playlist", cleaned

    # Aparat video hashes are alphanumeric strings (e.g. 'nbl9l8o')
    if re.match(r"^[a-zA-Z0-9_-]{4,30}$", cleaned):
        return "video", cleaned

    raise ValueError(f"Invalid Aparat input: '{input_str}'")


def _parse_quality_height(profile_str: Optional[str]) -> int:
    """Extract numeric resolution height from profile string (e.g. '720p' -> 720)."""
    if not profile_str:
        return 0
    match = re.search(r"(\d+)", str(profile_str))
    return int(match.group(1)) if match else 0


def get_available_qualities(videos: List[Dict[str, Any]]) -> List[str]:
    """Return unique qualities found across all videos sorted descending by resolution."""
    found: set[str] = set()
    for video in videos:
        for q in video.get("qualities", []):
            profile = q.get("profile")
            if profile:
                found.add(profile)

    return sorted(found, key=lambda p: (_parse_quality_height(p), p), reverse=True)


def resolve_download_link(
    video: Dict[str, Any], preferred_quality: Optional[str]
) -> Tuple[str, str, bool]:
    """Resolve download URL and profile for a video given a preferred quality.

    Returns (download_url, resolved_profile, is_fallback):
      - If preferred_quality is 'best', empty, or None: picks highest available profile (is_fallback=False).
      - If preferred_quality matches a profile: picks that URL (is_fallback=False).
      - Otherwise: falls back to highest available profile (is_fallback=True).

    Raises ValueError if video has no available qualities.
    """
    qualities = video.get("qualities") or []
    valid_qualities = [q for q in qualities if q.get("urls") and len(q["urls"]) > 0]
    if not valid_qualities:
        uid = video.get("uid", "unknown")
        raise ValueError(f"No download qualities available for video: {uid}")

    # Sort descending by resolution height
    sorted_qualities = sorted(
        valid_qualities,
        key=lambda q: (_parse_quality_height(q.get("profile", "")), q.get("profile", "")),
        reverse=True,
    )
    highest = sorted_qualities[0]

    # Best available quality requested
    if not preferred_quality or preferred_quality.strip().lower() == "best":
        return highest["urls"][0], highest["profile"], False

    norm_preferred = preferred_quality.strip().lower()

    # Exact match check
    for q in sorted_qualities:
        prof = q.get("profile", "").lower()
        if prof == norm_preferred or (
            norm_preferred.isdigit() and prof == f"{norm_preferred}p"
        ):
            return q["urls"][0], q["profile"], False

    # Fallback to highest available profile
    return highest["urls"][0], highest["profile"], True


def export_links_to_txt(
    videos: List[Dict[str, Any]],
    preferred_quality: Optional[str],
    output_file: str,
) -> int:
    """Export resolved download links for videos to a formatted text file.

    Format:
    # {video title} - {resolved profile}
    {download url}

    Returns count of successfully exported links.
    """
    dir_path = os.path.dirname(os.path.abspath(output_file))
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)

    count = 0
    with open(output_file, "w", encoding="utf-8") as f:
        for video in videos:
            try:
                url, profile, _ = resolve_download_link(video, preferred_quality)
                title = sanitize_filename(video.get("title") or "Video")
                f.write(f"# {title} - {profile}\n{url}\n\n")
                count += 1
            except ValueError:
                continue

    return count


class AparatClient:
    """Client for querying Aparat API and downloading video content."""

    def __init__(self, session: Optional[requests.Session] = None) -> None:
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": DEFAULT_USER_AGENT})
        self.logger = logging.getLogger("AparatClient")

    def _extract_next_url(self, data: Dict[str, Any]) -> Optional[str]:
        """Extract pagination next URL from Aparat JSON-API response."""
        # Check top-level links
        links = data.get("links")
        if isinstance(links, dict):
            nxt = links.get("next") or links.get("link_next")
            if nxt:
                return nxt

        # Check data.attributes
        attrs = data.get("data", {}).get("attributes", {})
        if isinstance(attrs, dict):
            nxt = attrs.get("link_next") or attrs.get("next")
            if nxt:
                return nxt

        # Check data.relationships.video.links
        rel_links = (
            data.get("data", {})
            .get("relationships", {})
            .get("video", {})
            .get("links", {})
        )
        if isinstance(rel_links, dict):
            nxt = rel_links.get("next") or rel_links.get("link_next")
            if nxt:
                return nxt

        return None

    def fetch_target(self, identifier: str, target_type: str) -> Dict[str, Any]:
        """Fetch metadata for a playlist or single video.

        Returns a dictionary with:
          - 'type': 'playlist' | 'video'
          - 'id': identifier string
          - 'title': playlist or video title
          - 'channel_name': channel title
          - 'videos': list of video dicts, each with:
              'uid', 'title', 'duration', 'duration_formatted', 'qualities', 'poster'
        """
        if target_type == "playlist":
            return self._fetch_playlist(identifier)
        elif target_type == "video":
            return self._fetch_single_video(identifier)
        else:
            raise ValueError(f"Unknown target_type: {target_type}")

    # Alias for convenience
    fetch_info = fetch_target

    def _fetch_playlist(self, playlist_id: str) -> Dict[str, Any]:
        """Fetch all videos in a playlist, following pagination if present."""
        api_url: Optional[str] = (
            f"https://www.aparat.com/api/fa/v1/video/playlist/one/playlist_id/{playlist_id}"
        )
        videos: List[Dict[str, Any]] = []
        title = f"Playlist {playlist_id}"
        channel_name = ""
        seen_uids: set[str] = set()

        while api_url:
            if not api_url.startswith("http"):
                api_url = urllib.parse.urljoin("https://www.aparat.com", api_url)

            resp = self.session.get(api_url, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            # Parse title and channel on first page
            attrs = data.get("data", {}).get("attributes", {})
            if attrs.get("title"):
                title = html.unescape(attrs["title"])
            if attrs.get("channel_name"):
                channel_name = html.unescape(attrs["channel_name"])
            elif attrs.get("sender_name"):
                channel_name = html.unescape(attrs["sender_name"])

            # Channel fallback from included items
            included = data.get("included", [])
            if not channel_name:
                for item in included:
                    if item.get("type") == "channel":
                        name = item.get("attributes", {}).get("name") or item.get(
                            "attributes", {}
                        ).get("title")
                        if name:
                            channel_name = html.unescape(name)
                            break

            # Parse video items
            for item in included:
                if item.get("type") == "Video":
                    v_attrs = item.get("attributes", {})
                    uid = v_attrs.get("uid") or item.get("id")
                    if not uid or uid in seen_uids:
                        continue
                    seen_uids.add(uid)

                    v_title = html.unescape(v_attrs.get("title") or "untitled")
                    try:
                        duration = int(float(v_attrs.get("duration") or 0))
                    except (ValueError, TypeError):
                        duration = 0
                    poster = (
                        v_attrs.get("big_poster")
                        or v_attrs.get("medium_poster")
                        or v_attrs.get("small_poster")
                        or ""
                    )
                    qualities = v_attrs.get("file_link_all") or []

                    videos.append(
                        {
                            "uid": uid,
                            "title": v_title,
                            "duration": duration,
                            "duration_formatted": format_duration(duration),
                            "qualities": qualities,
                            "poster": poster,
                        }
                    )

            # Check pagination
            next_url = self._extract_next_url(data)
            if next_url and next_url != api_url:
                api_url = next_url
            else:
                api_url = None

        return {
            "type": "playlist",
            "id": playlist_id,
            "title": title,
            "channel_name": channel_name,
            "videos": videos,
        }

    def _fetch_single_video(self, video_uid: str) -> Dict[str, Any]:
        """Fetch metadata and qualities for a single video."""
        api_url = (
            f"https://www.aparat.com/api/fa/v1/video/video/show/videohash/{video_uid}"
        )
        resp = self.session.get(api_url, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        attrs = data.get("data", {}).get("attributes", {})
        title = html.unescape(attrs.get("title") or f"video_{video_uid}")
        try:
            duration = int(float(attrs.get("duration") or 0))
        except (ValueError, TypeError):
            duration = 0
        poster = (
            attrs.get("big_poster")
            or attrs.get("medium_poster")
            or attrs.get("small_poster")
            or ""
        )
        qualities = attrs.get("file_link_all") or []

        # Find channel name
        channel_name = ""
        for item in data.get("included", []):
            if item.get("type") == "channel":
                name = item.get("attributes", {}).get("name") or item.get(
                    "attributes", {}
                ).get("title")
                if name:
                    channel_name = html.unescape(name)
                    break

        if not channel_name:
            channel_name = html.unescape(
                attrs.get("sender_name") or attrs.get("owner_username") or ""
            )

        video_dict = {
            "uid": video_uid,
            "title": title,
            "duration": duration,
            "duration_formatted": format_duration(duration),
            "qualities": qualities,
            "poster": poster,
        }

        return {
            "type": "video",
            "id": video_uid,
            "title": title,
            "channel_name": channel_name,
            "videos": [video_dict],
        }

    def _fetch_qualities_for_single_video(self, video: Dict[str, Any]) -> None:
        """Fetch qualities for a single video dictionary in-place."""
        if video.get("qualities"):
            return
        uid = video.get("uid")
        if not uid:
            return
        api_url = f"https://www.aparat.com/api/fa/v1/video/video/show/videohash/{uid}"
        try:
            resp = self.session.get(api_url, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                attrs = data.get("data", {}).get("attributes", {})
                video["qualities"] = attrs.get("file_link_all") or []
        except Exception as err:
            self.logger.warning(f"Failed to fetch qualities for video {uid}: {err}")
            video["qualities"] = []

    def fetch_all_video_qualities(
        self,
        videos: List[Dict[str, Any]],
        max_workers: int = 5,
        progress_cb: Optional[Callable[[int, int], None]] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch download qualities for all videos concurrently using ThreadPoolExecutor."""
        total = len(videos)
        if total == 0:
            return videos

        completed = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_video = {
                executor.submit(self._fetch_qualities_for_single_video, video): video
                for video in videos
            }
            for future in concurrent.futures.as_completed(future_to_video):
                completed += 1
                try:
                    future.result()
                except Exception as err:
                    vid = future_to_video[future].get("uid", "unknown")
                    self.logger.warning(f"Error fetching qualities for {vid}: {err}")
                if progress_cb:
                    progress_cb(completed, total)

        return videos

    def download_video(
        self,
        url: str,
        output_path: str,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        cancel_token: Optional[CancellationToken] = None,
    ) -> bool:
        """Stream download video content to output_path with progress and cancellation.

        progress_callback signature: (bytes_downloaded, total_bytes, speed_bytes_per_sec)
        Returns True if download completed successfully, False if cancelled or interrupted.
        """
        dir_path = os.path.dirname(os.path.abspath(output_path))
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

        if cancel_token and cancel_token.is_cancelled():
            return False

        resp = self.session.get(url, stream=True, timeout=30)
        resp.raise_for_status()

        try:
            total_bytes = int(resp.headers.get("content-length", 0))
        except (ValueError, TypeError):
            total_bytes = 0
        bytes_downloaded = 0
        start_time = time.monotonic()
        last_time = start_time
        last_bytes = 0
        speed = 0.0

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=CHUNK_SIZE):
                if cancel_token and cancel_token.is_cancelled():
                    return False

                if chunk:
                    f.write(chunk)
                    bytes_downloaded += len(chunk)
                    now = time.monotonic()
                    dt = now - last_time

                    if dt >= 0.2:  # Update speed metric every 200ms
                        speed = (bytes_downloaded - last_bytes) / dt
                        last_time = now
                        last_bytes = bytes_downloaded

                    if progress_callback:
                        progress_callback(bytes_downloaded, total_bytes, speed)

        # Final 100% callback invocation
        if progress_callback and total_bytes > 0:
            elapsed = time.monotonic() - start_time
            final_speed = bytes_downloaded / elapsed if elapsed > 0 else 0.0
            progress_callback(bytes_downloaded, total_bytes, final_speed)

        return True

    # Delegate methods to module-level functions
    get_available_qualities = staticmethod(get_available_qualities)
    resolve_download_link = staticmethod(resolve_download_link)
    export_links_to_txt = staticmethod(export_links_to_txt)
    parse_aparat_input = staticmethod(parse_aparat_input)
    sanitize_filename = staticmethod(sanitize_filename)


class AparatDownloader:
    """Backwards-compatible wrapper around AparatClient for legacy scripts and GUI."""

    def __init__(
        self,
        playlist_id: Optional[str] = None,
        quality: Optional[str] = None,
        for_download_manager: bool = False,
        destination_path: str = "Downloads",
    ) -> None:
        self.playlist_id = playlist_id
        self.quality = quality
        self.for_download_manager = for_download_manager
        self.destination_path = destination_path
        self.current_directory = os.getcwd()
        self.logger = self.setup_logger()
        self.client = AparatClient()

        if not os.path.exists(destination_path):
            os.makedirs(destination_path, exist_ok=True)

    @staticmethod
    def setup_logger() -> logging.Logger:
        """Create or retrieve a standard logger."""
        logger = logging.getLogger("AparatDownloader")
        if not logger.handlers:
            logger.setLevel(logging.INFO)
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        return logger

    def download_video(self, video_url: str, output_path: str) -> None:
        """Download video directly using the client."""
        try:
            success = self.client.download_video(video_url, output_path)
            if success:
                full_output_path = os.path.join(self.current_directory, output_path)
                self.logger.info(f"Downloaded to {full_output_path}")
            else:
                self.logger.warning("Download was cancelled or interrupted.")
        except Exception as e:
            self.logger.error(f"Failed to download the video: {e}")

    @staticmethod
    def get_video_download_urls(video_uid: str) -> List[Dict[str, Any]]:
        """Legacy helper to get raw download URLs for a video hash."""
        client = AparatClient()
        target = client.fetch_target(video_uid, "video")
        if target.get("videos"):
            return target["videos"][0].get("qualities", [])
        return []

    def download_playlist(self) -> None:
        """Download or export all playlist items matching the requested quality."""
        assert self.playlist_id is not None, "playlist_id must not be None"
        assert self.quality is not None, "quality must not be None"

        try:
            target = self.client.fetch_target(self.playlist_id, "playlist")
            videos = target.get("videos", [])
            raw_title = target.get("title", f"playlist_{self.playlist_id}")
            safe_title = sanitize_filename(raw_title)

            # Resolve all qualities concurrently
            self.client.fetch_all_video_qualities(videos)

            if self.for_download_manager:
                self.logger.info(f"Start creating {safe_title}.txt file")
                txt_path = os.path.join(self.destination_path, f"{safe_title}.txt")
                self.client.export_links_to_txt(videos, self.quality, txt_path)
                self.logger.info(f"{safe_title}.txt created")
            else:
                self.logger.info(f"Downloading Playlist {raw_title} ...")
                playlist_folder = os.path.join(self.destination_path, safe_title)
                os.makedirs(playlist_folder, exist_ok=True)

                quality_str = (self.quality or "").rstrip("p") + "p"
                for video in videos:
                    try:
                        video_title = sanitize_filename(video.get("title", "video"))
                        url, profile, is_fallback = self.client.resolve_download_link(
                            video, self.quality
                        )
                        if is_fallback:
                            self.logger.warning(
                                f"Quality '{quality_str}' unavailable for '{video_title}', falling back to {profile}"
                            )
                        output_file = os.path.join(
                            playlist_folder, f"{video_title}-{profile}.mp4"
                        )
                        self.download_video(url, output_file)
                    except Exception as err:
                        self.logger.error(
                            f"Failed to download video '{video.get('title', 'unknown')}': {err}"
                        )

        except KeyError:
            self.logger.error("We have some errors in getting API data!")
        except requests.exceptions.ConnectionError:
            self.logger.error("Please check your internet connection.")
        except Exception as e:
            self.logger.error(str(e))
