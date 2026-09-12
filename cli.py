"""Modern interactive and scriptable CLI for Aparat Downloader v1.0.0.

Maintained by Ali Bakhtiari.
"""

from __future__ import annotations

__version__ = "1.0.0"

import argparse
import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from core import (
    AparatClient,
    format_duration,
    get_available_qualities,
    parse_aparat_input,
    sanitize_filename,
)

BANNER = """========================================================
         Aparat Downloader v1.0.0 - CLI Edition
               Maintained by Ali Bakhtiari
========================================================"""


def configure_terminal_encoding() -> None:
    """Ensure standard output and error support UTF-8 for Persian/Unicode titles."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass


def format_bytes(bytes_count: float | int) -> str:
    """Format byte counts into human-readable strings (B, KB, MB, GB)."""
    val = float(bytes_count)
    if val < 1024.0:
        return f"{val:.1f} B"
    val /= 1024.0
    if val < 1024.0:
        return f"{val:.1f} KB"
    val /= 1024.0
    if val < 1024.0:
        return f"{val:.1f} MB"
    val /= 1024.0
    return f"{val:.1f} GB"


def format_progress_bar(
    current_bytes: int,
    total_bytes: int,
    speed_bytes_per_sec: float,
    current_item: Optional[int] = None,
    total_items: Optional[int] = None,
    bar_width: int = 20,
) -> str:
    """Format a clean in-place terminal progress bar."""
    prefix = (
        f"[Video {current_item}/{total_items}] "
        if current_item is not None and total_items is not None
        else ""
    )

    spd_str = f"{format_bytes(speed_bytes_per_sec)}/s"
    cur_str = format_bytes(current_bytes)

    if total_bytes > 0:
        fraction = min(1.0, max(0.0, current_bytes / total_bytes))
        percent = fraction * 100.0
        filled_len = int(bar_width * fraction)
        bar = "█" * filled_len + "░" * (bar_width - filled_len)
        tot_str = format_bytes(total_bytes)
        return f"{prefix}[{bar}] {percent:.1f}% ({cur_str} / {tot_str}) - {spd_str}"
    else:
        bar = "░" * bar_width
        return f"{prefix}[{bar}] --.-% ({cur_str} / Unknown) - {spd_str}"


def format_video_table(videos: List[Dict[str, Any]]) -> str:
    """Render a clean text table listing videos with duration, qualities, and titles."""
    if not videos:
        return "No videos to display."

    lines: List[str] = []
    idx_width = max(3, len(str(len(videos))))
    dur_width = 8
    qual_width = 35

    header = (
        f"{'#':<{idx_width}} | {'Duration':<{dur_width}} | "
        f"{'Qualities Available':<{qual_width}} | Title"
    )
    separator = (
        f"{'-' * idx_width}-+-{'-' * dur_width}-+-"
        f"{'-' * qual_width}-+-{'-' * 30}"
    )
    lines.append(header)
    lines.append(separator)

    for idx, video in enumerate(videos, start=1):
        dur = video.get("duration_formatted") or format_duration(
            video.get("duration", 0)
        )
        profiles: List[str] = [
            q.get("profile")
            for q in video.get("qualities", [])
            if q.get("profile")
        ]

        def _sort_profile(p: str) -> int:
            match = re.search(r"(\d+)", p)
            return int(match.group(1)) if match else 0

        sorted_profiles = sorted(profiles, key=_sort_profile)
        qual_str = ", ".join(sorted_profiles) if sorted_profiles else "-"
        title = video.get("title", "untitled")

        lines.append(
            f"{idx:<{idx_width}} | {dur:<{dur_width}} | "
            f"{qual_str:<{qual_width}} | {title}"
        )

    return "\n".join(lines)


def build_quality_options(available_qualities: List[str]) -> List[Tuple[str, str]]:
    """Build list of (choice_number, label) pairs for quality selection."""
    options: List[Tuple[str, str]] = [
        ("1", "Best Available (Highest quality for each video) [Recommended]")
    ]

    for idx, q in enumerate(available_qualities):
        choice_num = str(idx + 2)
        if idx == 0:
            label = f"{q} (with fallback to highest if unavailable)"
        else:
            label = f"{q} (with fallback)"
        options.append((choice_num, label))

    return options


def resolve_quality_choice(
    choice_str: str, available_qualities: List[str]
) -> Optional[str]:
    """Parse and resolve user quality input to 'best' or a specific quality string."""
    cleaned = choice_str.strip()
    if not cleaned or cleaned.lower() == "best" or cleaned == "1":
        return "best"

    cleaned_lower = cleaned.lower()
    if cleaned_lower.endswith("p"):
        norm = cleaned_lower
    else:
        norm = f"{cleaned_lower}p"

    # 1. Direct match with available quality name (e.g. '720p' or '720')
    for q in available_qualities:
        if cleaned_lower == q.lower() or norm == q.lower():
            return q

    # 2. Numbered menu choice (e.g. '2' for second option)
    if cleaned.isdigit():
        num = int(cleaned)
        if 2 <= num <= len(available_qualities) + 1:
            return available_qualities[num - 2]

    # 3. Arbitrary realistic resolution pattern (e.g. '720' -> '720p' or '1080p')
    if re.match(r"^\d{3,4}p?$", cleaned_lower):
        return norm

    return None


def resolve_action_choice(choice_str: str) -> Optional[str]:
    """Resolve action choice string to 'download' or 'export'."""
    cleaned = choice_str.strip().lower()
    if not cleaned or cleaned in ("1", "download", "d"):
        return "download"
    if cleaned in ("2", "export", "e", "txt"):
        return "export"
    return None


def parse_cli_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Aparat Playlist & Video Downloader CLI Edition v1.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Maintained by Ali Bakhtiari",
    )
    parser.add_argument(
        "url_or_id",
        nargs="?",
        default=None,
        help="Aparat playlist or video URL or ID",
    )
    parser.add_argument(
        "-q",
        "--quality",
        default=None,
        help="Preferred video quality (e.g. 1080, 720, 480, 360, best)",
    )
    parser.add_argument(
        "-e",
        "--export",
        action="store_true",
        help="Export direct download links to a .txt file instead of downloading",
    )
    parser.add_argument(
        "-d",
        "--dest",
        default=None,
        help="Destination directory for downloads or exported .txt file",
    )
    return parser.parse_args(args)


def prompt_quality_interactive(
    available_qualities: List[str], input_fn: Optional[Callable[[str], str]] = None
) -> str:
    """Prompt user to choose quality with numbered options."""
    _input = input_fn if input_fn is not None else input
    options = build_quality_options(available_qualities)
    print("\nAvailable Qualities:")
    for num, label in options:
        print(f"  [{num}] {label}")

    max_choice = len(options)
    while True:
        try:
            choice = _input(f"Choice (1-{max_choice}) [default: 1]: ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(130)

        resolved = resolve_quality_choice(choice, available_qualities)
        if resolved:
            return resolved
        print(f"Invalid choice '{choice}'. Please select 1-{max_choice} or quality name.")


def prompt_action_interactive(input_fn: Optional[Callable[[str], str]] = None) -> str:
    """Prompt user to select action (download vs export links)."""
    _input = input_fn if input_fn is not None else input
    print("\nSelect Action:")
    print("  [1] Download video(s)")
    print("  [2] Export download links to .txt file")

    while True:
        try:
            choice = _input("Choice (1-2) [default: 1]: ")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            sys.exit(130)

        action = resolve_action_choice(choice)
        if action:
            return action
        print(f"Invalid choice '{choice}'. Please enter 1 or 2.")


def prompt_destination_interactive(
    default_dest: str = "./Downloads", input_fn: Optional[Callable[[str], str]] = None
) -> str:
    """Prompt user for destination directory."""
    _input = input_fn if input_fn is not None else input
    try:
        dest = _input(f"\nEnter destination path (default: {default_dest}): ")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled.")
        sys.exit(130)

    cleaned = dest.strip()
    return cleaned if cleaned else default_dest


def execute_export(
    videos: List[Dict[str, Any]],
    preferred_quality: str,
    target: Dict[str, Any],
    destination_path: str,
    client: AparatClient,
) -> int:
    """Export download links to a text file."""
    raw_title = target.get("title") or target.get("id") or "aparat_export"
    safe_title = sanitize_filename(raw_title)
    os.makedirs(destination_path, exist_ok=True)
    output_filepath = os.path.join(destination_path, f"{safe_title}.txt")

    count = client.export_links_to_txt(videos, preferred_quality, output_filepath)
    abs_path = os.path.abspath(output_filepath)
    print(f"\n[Success] Exported {count} link(s) to:\n  {abs_path}")
    return count


def execute_download(
    videos: List[Dict[str, Any]],
    preferred_quality: str,
    target: Dict[str, Any],
    destination_path: str,
    client: AparatClient,
) -> bool:
    """Download videos with smooth progress updates and fallback handling."""
    target_type = target.get("type", "playlist")
    total_videos = len(videos)

    if target_type == "playlist":
        safe_playlist_title = sanitize_filename(
            target.get("title") or f"playlist_{target.get('id', 'unknown')}"
        )
        output_dir = os.path.join(destination_path, safe_playlist_title)
    else:
        output_dir = destination_path

    os.makedirs(output_dir, exist_ok=True)
    print(f"\nStarting download to: {os.path.abspath(output_dir)}\n")

    overall_success = True
    for idx, video in enumerate(videos, start=1):
        vid_title = sanitize_filename(video.get("title") or f"video_{idx}")
        try:
            url, profile, is_fallback = client.resolve_download_link(
                video, preferred_quality
            )
        except ValueError as err:
            print(f"[Video {idx}/{total_videos}] Error resolving quality: {err}")
            overall_success = False
            continue

        if is_fallback:
            print(
                f"[Video {idx}/{total_videos}] Quality '{preferred_quality}' unavailable, "
                f"falling back to {profile}."
            )

        video_filename = f"{vid_title} - {profile}.mp4"
        video_filepath = os.path.join(output_dir, video_filename)

        last_len = [0]

        def progress_cb(
            current_bytes: int, total_bytes: int, speed: float
        ) -> None:
            bar_text = format_progress_bar(
                current_bytes=current_bytes,
                total_bytes=total_bytes,
                speed_bytes_per_sec=speed,
                current_item=idx,
                total_items=total_videos,
            )
            pad = max(0, last_len[0] - len(bar_text))
            sys.stdout.write(f"\r{bar_text}{' ' * pad}")
            sys.stdout.flush()
            last_len[0] = len(bar_text)

        try:
            success = client.download_video(
                url, video_filepath, progress_callback=progress_cb
            )
            sys.stdout.write("\n")
            sys.stdout.flush()
            if success:
                print(f"[Video {idx}/{total_videos}] Finished: {video_filename}")
            else:
                print(f"[Video {idx}/{total_videos}] Cancelled: {video_filename}")
                overall_success = False
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
            print("\nDownload interrupted by user.")
            raise
        except Exception as err:
            sys.stdout.write("\n")
            sys.stdout.flush()
            print(f"[Video {idx}/{total_videos}] Failed: {err}")
            overall_success = False

    return overall_success


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    configure_terminal_encoding()
    args = parse_cli_args(argv)

    client = AparatClient()

    # Interactive mode check
    if not args.url_or_id:
        print(BANNER)
        while True:
            try:
                user_input = input(
                    "\nEnter Aparat Playlist or Video URL/ID (or 'q' to exit): "
                )
            except (KeyboardInterrupt, EOFError):
                print("\nExiting...")
                return 0

            cleaned = user_input.strip()
            if cleaned.lower() in ("q", "quit", "exit"):
                print("Exiting...")
                return 0

            try:
                target_type, identifier = parse_aparat_input(cleaned)
                break
            except ValueError as err:
                print(f"Invalid Aparat URL or ID: {err}. Please try again.")
    else:
        try:
            target_type, identifier = parse_aparat_input(args.url_or_id)
        except ValueError as err:
            print(f"Error: {err}")
            return 1

    # Fetch metadata
    print("\nFetching metadata...")
    try:
        target = client.fetch_target(identifier, target_type)
    except Exception as err:
        print(f"Error fetching metadata: {err}")
        return 1

    videos = target.get("videos", [])
    if not videos:
        print("No videos found.")
        return 1

    # Fetch qualities concurrently
    total_videos = len(videos)
    last_len = [0]

    def quality_cb(completed: int, total: int) -> None:
        msg = f"Fetching qualities: [{completed}/{total}]"
        pad = max(0, last_len[0] - len(msg))
        sys.stdout.write(f"\r{msg}{' ' * pad}")
        sys.stdout.flush()
        last_len[0] = len(msg)

    client.fetch_all_video_qualities(videos, progress_cb=quality_cb)
    sys.stdout.write("\n")
    sys.stdout.flush()

    # Print Summary
    channel_name = target.get("channel_name") or "Unknown"
    title = target.get("title") or "Untitled"
    if target_type == "playlist":
        type_str = f"Playlist ({total_videos} video{'s' if total_videos != 1 else ''})"
    else:
        type_str = "Single Video"

    print("\nSummary:")
    print(f"  Title:   {title}")
    print(f"  Channel: {channel_name}")
    print(f"  Type:    {type_str}\n")

    # Print Video Listing Table
    print(format_video_table(videos))

    available_qualities = get_available_qualities(videos)

    # Determine Quality
    if args.quality:
        preferred_quality = args.quality
    elif not args.url_or_id:
        preferred_quality = prompt_quality_interactive(available_qualities)
    else:
        preferred_quality = "best"

    # Determine Action
    if args.export:
        action = "export"
    elif not args.url_or_id:
        action = prompt_action_interactive()
    else:
        action = "download"

    # Determine Destination
    if args.dest:
        dest_path = args.dest
    elif not args.url_or_id:
        dest_path = prompt_destination_interactive()
    else:
        dest_path = "./Downloads"

    # Execute
    try:
        if action == "export":
            count = execute_export(videos, preferred_quality, target, dest_path, client)
            return 0 if count > 0 else 1
        else:
            success = execute_download(videos, preferred_quality, target, dest_path, client)
            return 0 if success else 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
