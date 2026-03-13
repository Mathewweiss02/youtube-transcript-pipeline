#!/usr/bin/env python3
"""Shared helpers for the collection-first transcript pipeline."""

from __future__ import annotations

import fnmatch
import functools
import glob
import hashlib
import json
import os
import re
import subprocess
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TRANSCRIPTS_ROOT = REPO_ROOT / "transcripts"
COLLECTION_REGISTRY_PATH = SCRIPT_DIR / "collection_registry.json"
LEGACY_REGISTRY_PATH = SCRIPT_DIR / "channel_registry.json"
PENDING_PATH = SCRIPT_DIR / "pending_updates.json"
PROVENANCE_DIR = SCRIPT_DIR / "provenance_manifests"
OVERRIDES_DIR = SCRIPT_DIR / "provenance_overrides"
REPORTS_DIR = SCRIPT_DIR / "reports"
APP_SIDECAR_PATH = REPO_ROOT / "youtuber wiki apps" / "my-app" / "data" / "transcript-video-sidecars.json"
MAX_CHUNK_SIZE = int(2.4 * 1024 * 1024)

URL_RE = re.compile(r"https?://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})")
URL_VALUE_RE = re.compile(r"(https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]{11})")
ANCHOR_RE = re.compile(r"<a[^>]*></a>")
ANCHOR_BLOCK_RE = re.compile(
    r"<a[^>]*></a>\s*(?P<title>.+?)\s*(?P<url>https?://(?:www\.)?youtube\.com/watch\?v=[A-Za-z0-9_-]{11})",
    re.DOTALL,
)
HEADING_RE = re.compile(r"^(#{1,6})\s*(.+)$")
TOC_BULLET_RE = re.compile(r"^-\s+(?:\[[^\]]+\]\([^)]+\)\s*)?(.+)$")
TOC_NUMBERED_RE = re.compile(r"^\d+\.\s+(.+)$")
SEPARATOR_RE = re.compile(r"^[-=]{3,}\s*$")
SLASH_VARIANTS = r"[\u002f\u2044\u2215\u2571\u29f8\uff0f]"
BAR_VARIANTS = r"[\u007c\uff5c]"


def _find_yt_dlp() -> str:
    base_dir = "C:/yt-dlp"
    try:
        if os.path.isdir(base_dir):
            for name in os.listdir(base_dir):
                lower = name.lower()
                if lower.startswith("yt-dlp") and lower.endswith(".exe"):
                    return os.path.join(base_dir, name)
    except OSError:
        pass

    scripts_dir = os.path.join(os.path.dirname(sys.executable), "Scripts")
    candidate = os.path.join(scripts_dir, "yt-dlp.exe")
    if os.path.exists(candidate):
        return candidate

    winget_base = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages")
    if os.path.isdir(winget_base):
        for folder in os.listdir(winget_base):
            if "yt-dlp" not in folder.lower():
                continue
            winget_exe = os.path.join(winget_base, folder, "yt-dlp.exe")
            if os.path.exists(winget_exe):
                return winget_exe

    env_path = os.environ.get("YT_DLP_PATH")
    if env_path:
        return env_path

    return "yt-dlp"


YT_DLP_PATH = _find_yt_dlp()


def ensure_output_dirs():
    PROVENANCE_DIR.mkdir(parents=True, exist_ok=True)
    OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default=None):
    if not path.exists():
        return {} if default is None else default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def load_collection_registry() -> dict[str, dict]:
    if not COLLECTION_REGISTRY_PATH.exists():
        raise FileNotFoundError(f"Collection registry not found: {COLLECTION_REGISTRY_PATH}")
    payload = load_json(COLLECTION_REGISTRY_PATH, default={"collections": {}})
    return payload.get("collections", {})


def load_legacy_registry() -> dict[str, dict]:
    if not LEGACY_REGISTRY_PATH.exists():
        return {}
    payload = load_json(LEGACY_REGISTRY_PATH, default={"channels": {}})
    return payload.get("channels", {})


def load_collection_overrides(collection_key: str) -> dict:
    path = OVERRIDES_DIR / f"{collection_key}.json"
    default = {
        "ignored_files": [],
        "ignored_titles": [],
        "bundle_file_overrides": {},
        "entries": {},
        "manual_notes": [],
    }
    if not path.exists():
        return default

    payload = load_json(path, default=default)
    for key, value in default.items():
        payload.setdefault(key, value)
    return payload


def resolve_repo_path(path_value: str) -> Path:
    return (REPO_ROOT / path_value).resolve()


def resolve_collection_transcript_dir(collection: dict) -> Path:
    return resolve_repo_path(collection["transcript_dir"])


def resolve_collection_raw_dir(collection: dict) -> Path | None:
    raw_dir = collection.get("raw_dir")
    if not raw_dir:
        return None
    return resolve_repo_path(raw_dir)


def resolve_manifest_path(collection: dict) -> Path:
    return resolve_repo_path(collection["provenance_manifest"])


def clean_title(value: str) -> str:
    normalized = value.strip()
    normalized = ANCHOR_RE.sub("", normalized)
    normalized = re.sub(r"^#{1,6}\s+", "", normalized)
    normalized = re.sub(r"^\d+\s*[\.\)]\s+", "", normalized)
    normalized = re.sub(r"^mindpump[_\s-]+", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^Video\s+\d+\s*:\s*", "", normalized, flags=re.IGNORECASE)
    normalized = re.sub(r"^\d+\s*[-:]\s+", "", normalized)
    normalized = re.sub(r"\.en$", "", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace("&amp;", "&")
    normalized = unicodedata.normalize("NFKC", normalized)
    normalized = unicodedata.normalize("NFKD", normalized)
    normalized = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    normalized = normalized.replace("&", " and ")
    normalized = re.sub(rf"\bw\s*{SLASH_VARIANTS}\s*", " with ", normalized, flags=re.IGNORECASE)
    normalized = re.sub(
        rf"\s*{BAR_VARIANTS}\s*(the\s+)?jay\s+campbell\s+(podcast|pc)\b",
        "",
        normalized,
        flags=re.IGNORECASE,
    )
    normalized = re.sub(r"['\"`]", "", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def normalize_title(value: str) -> str:
    normalized = clean_title(value)
    normalized = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return normalized


def extract_video_id(url: str) -> str:
    match = URL_RE.search(url)
    return match.group(1) if match else ""


def build_channel_video_url(channel_url: str) -> str:
    trimmed = channel_url.strip().rstrip("/")
    if not trimmed:
        return trimmed
    if trimmed.endswith("/videos"):
        return trimmed
    if re.match(r"^https?://(?:www\.)?youtube\.com/@[^/\s]+$", trimmed):
        return trimmed + "/videos"
    if re.match(r"^https?://(?:www\.)?youtube\.com/channel/[^/\s]+$", trimmed):
        return trimmed + "/videos"
    return trimmed


@functools.lru_cache(maxsize=128)
def fetch_channel_videos(channel_url: str) -> list[dict]:
    if not channel_url:
        return []

    cmd = [
        YT_DLP_PATH,
        "--flat-playlist",
        "--dump-single-json",
        "--no-warnings",
        build_channel_video_url(channel_url),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
            check=True,
        )
        payload = json.loads(result.stdout)
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, json.JSONDecodeError):
        return []

    if payload.get("_type") == "url" and payload.get("url"):
        try:
            result = subprocess.run(
                [YT_DLP_PATH, "--flat-playlist", "--dump-single-json", "--no-warnings", payload["url"]],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                check=True,
            )
            payload = json.loads(result.stdout)
        except Exception:
            return []

    entries = payload.get("entries") or []
    videos: list[dict] = []
    for entry in entries:
        video_id = entry.get("id") or ""
        title = entry.get("title") or ""
        if not video_id or not title:
            continue

        url = f"https://www.youtube.com/watch?v={video_id}"
        duration = entry.get("duration")
        entry_url = entry.get("url") or url
        if "/shorts/" in entry_url:
            continue
        if duration is not None:
            try:
                if float(duration) <= 60:
                    continue
            except (TypeError, ValueError):
                pass

        videos.append(
            {
                "id": video_id,
                "title": title,
                "normalized_title": normalize_title(title),
                "url": url,
                "duration": duration,
            }
        )

    return videos


def build_live_video_index(source_channels: list[dict]) -> tuple[dict[str, list[dict]], dict[str, dict], dict[tuple[str, str], list[dict]]]:
    per_source: dict[str, list[dict]] = {}
    by_video_id: dict[str, dict] = {}
    by_source_and_title: dict[tuple[str, str], list[dict]] = {}

    for source in source_channels:
        source_key = source.get("key") or source.get("handle") or source.get("name") or "unknown"
        youtube_url = source.get("youtube_url", "")
        if not youtube_url:
            per_source[source_key] = []
            continue

        videos = fetch_channel_videos(youtube_url)
        for video in videos:
            record = dict(video)
            record["source_channel_key"] = source_key
            by_video_id[video["id"]] = record
            by_source_and_title.setdefault((source_key, video["normalized_title"]), []).append(record)
        per_source[source_key] = videos

    return per_source, by_video_id, by_source_and_title


def match_patterns(name: str, patterns: Iterable[str]) -> bool:
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def discover_bundle_files(collection: dict) -> list[Path]:
    transcript_dir = resolve_collection_transcript_dir(collection)
    if not transcript_dir.exists():
        return []
    return sorted(p for p in transcript_dir.glob("*.md") if p.is_file())


def resolve_canonical_source_files(collection: dict) -> list[Path]:
    transcript_dir = resolve_collection_transcript_dir(collection)
    if not transcript_dir.exists():
        return []

    patterns = collection.get("canonical_sources") or collection.get("scan_sources") or []
    matches: list[Path] = []
    for pattern in patterns:
        matches.extend(Path(p) for p in glob.glob(str(transcript_dir / pattern)))

    if not matches:
        chunk_pattern = collection.get("chunk_pattern")
        if chunk_pattern:
            matches.extend(Path(p) for p in glob.glob(str(transcript_dir / chunk_pattern)))

    if not matches:
        matches.extend(discover_bundle_files(collection))

    return sorted(set(matches))


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_bundle_override(file_name: str, overrides: dict) -> dict:
    result: dict = {}
    for pattern, payload in overrides.get("bundle_file_overrides", {}).items():
        if fnmatch.fnmatch(file_name, pattern):
            result.update(payload)
    return result


def classify_bundle_role(file_name: str, collection: dict, overrides: dict) -> str:
    override = get_bundle_override(file_name, overrides)
    if override.get("bundle_role"):
        return override["bundle_role"]

    if match_patterns(file_name, overrides.get("ignored_files", [])):
        return "reference_only"

    if file_name.lower().startswith(("index", "readme")):
        return "reference_only"

    canonical_sources = collection.get("canonical_sources") or []
    if match_patterns(file_name, canonical_sources):
        return "canonical_chunk"

    lower = file_name.lower()
    if lower.startswith("merged_") or "merged_all" in lower:
        return "legacy_merge"
    if "consolidated" in lower or "essentials" in lower or "series" in lower:
        return "topic_bundle"
    if "part_" in lower or "chunk_" in lower:
        return "canonical_chunk"
    return "topic_bundle"


def _clean_heading_title(raw: str) -> str:
    title = raw.strip()
    title = ANCHOR_RE.sub("", title)
    title = title.replace("&nbsp;", " ")
    title = title.strip("# ").strip()
    title = re.sub(r"\s+", " ", title).strip()
    return title


def _extract_title_and_url(raw: str, fallback_url: str = "") -> tuple[str, str]:
    working = raw.strip()
    inline_url = fallback_url
    url_match = URL_VALUE_RE.search(working)
    if url_match:
        inline_url = url_match.group(1)
        working = working[: url_match.start()]

    working = working.split("**YouTube:**", 1)[0]
    working = working.split("URL:", 1)[0]
    working = re.split(r"\s+#\s+", working, maxsplit=1)[0]
    working = re.split(r"\s+Duration:\s*", working, maxsplit=1)[0]
    working = re.split(r"(?<=\.en)(?=[A-Za-z])", working, maxsplit=1)[0]
    working = re.sub(r"\s+", " ", working).strip(" -:#")
    return _clean_heading_title(working), inline_url


def _parse_toc_title(line: str) -> str | None:
    for regex in (TOC_BULLET_RE, TOC_NUMBERED_RE):
        match = regex.match(line)
        if not match:
            continue
        raw = match.group(1).strip()
        raw = re.sub(r"\s*\([^)]*\)\s*$", "", raw)
        return _clean_heading_title(raw)
    return None


def _valid_title(title: str, ignored_titles: set[str]) -> bool:
    if not title:
        return False
    normalized = normalize_title(title)
    if not normalized:
        return False
    if normalized in ignored_titles:
        return False
    lowered = title.lower()
    if "table of contents" in lowered:
        return False
    if lowered in {"overview", "general discussion"}:
        return False
    return True


def extract_candidates_from_bundle(bundle_path: Path, ignored_titles: Iterable[str] | None = None) -> list[dict]:
    ignored = {normalize_title(value) for value in (ignored_titles or [])}
    text = bundle_path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    candidates: dict[str, dict] = {}
    current_key: str | None = None
    in_toc = False
    body_started = False

    def upsert_candidate(title: str, source_hint: str, line_number: int) -> str | None:
        cleaned = _clean_heading_title(title)
        if not _valid_title(cleaned, ignored):
            return None

        normalized = normalize_title(cleaned)
        candidate = candidates.get(normalized)
        if candidate is None:
            candidate = {
                "title": cleaned,
                "normalized_title": normalized,
                "bundle_file": bundle_path.name,
                "line_number": line_number,
                "source_hint": source_hint,
                "url": "",
                "video_id": "",
            }
            candidates[normalized] = candidate
        else:
            if len(cleaned) > len(candidate["title"]):
                candidate["title"] = cleaned
            if candidate["source_hint"] == "toc" and source_hint != "toc":
                candidate["title"] = cleaned
                candidate["source_hint"] = source_hint
                candidate["line_number"] = line_number
        return normalized

    for match in ANCHOR_BLOCK_RE.finditer(text):
        title, inline_url = _extract_title_and_url(match.group("title"), fallback_url=match.group("url"))
        line_number = text.count("\n", 0, match.start()) + 1
        key = upsert_candidate(title, "anchor_heading", line_number)
        if key and inline_url:
            candidates[key]["url"] = inline_url
            candidates[key]["video_id"] = extract_video_id(inline_url)

    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        lowered = stripped.lower()
        if "table of contents" in lowered:
            in_toc = True
            current_key = None
            continue

        if SEPARATOR_RE.match(stripped):
            if in_toc:
                in_toc = False
            # Some archives start immediately with a section separator and then
            # a video heading, with no wrapper H1/TOC block. Treat any
            # separator as proof that we are in body content.
            body_started = True
            current_key = None
            continue

        if in_toc:
            toc_title = _parse_toc_title(stripped)
            if toc_title:
                current_key = upsert_candidate(toc_title, "toc", index)
            continue

        if "<a " in stripped and "</a>" in stripped:
            current_key = None
            continue

        heading_match = HEADING_RE.match(stripped)
        if heading_match:
            level = len(heading_match.group(1))
            raw_title, inline_url = _extract_title_and_url(heading_match.group(2))
            if body_started or level >= 2:
                current_key = upsert_candidate(raw_title, "body_heading", index)
                if current_key and inline_url:
                    candidates[current_key]["url"] = inline_url
                    candidates[current_key]["video_id"] = extract_video_id(inline_url)
            continue

        url_match = URL_VALUE_RE.search(stripped)
        if url_match and current_key:
            inline_url = url_match.group(1)
            candidates[current_key]["url"] = inline_url
            candidates[current_key]["video_id"] = extract_video_id(inline_url)

    return list(candidates.values())


def build_bundle_records(collection: dict, overrides: dict) -> list[dict]:
    bundle_records: list[dict] = []
    default_source_keys = [source.get("key") for source in collection.get("source_channels", []) if source.get("key")]

    for path in discover_bundle_files(collection):
        override = get_bundle_override(path.name, overrides)
        source_keys = override.get("source_channel_keys") or default_source_keys
        bundle_records.append(
            {
                "path": str(path.relative_to(REPO_ROOT)),
                "sha256": compute_sha256(path),
                "size_bytes": path.stat().st_size,
                "bundle_role": classify_bundle_role(path.name, collection, overrides),
                "source_channel_keys": source_keys,
            }
        )

    return bundle_records


def summarize_confidence(entries: Iterable[dict]) -> dict[str, int]:
    summary = {"high": 0, "medium": 0, "manual_review": 0}
    for entry in entries:
        confidence = entry.get("confidence", "manual_review")
        summary[confidence] = summary.get(confidence, 0) + 1
    return summary


def unique_entries_by_video(entries: Iterable[dict]) -> list[dict]:
    seen_video_ids: set[str] = set()
    seen_titles: set[tuple[str, str]] = set()
    unique: list[dict] = []
    for entry in entries:
        video_id = entry.get("video_id") or ""
        source_key = entry.get("source_channel_key") or ""
        normalized = entry.get("normalized_title") or ""
        if video_id:
            if video_id in seen_video_ids:
                continue
            seen_video_ids.add(video_id)
            unique.append(entry)
            continue

        key = (source_key, normalized)
        if key in seen_titles:
            continue
        seen_titles.add(key)
        unique.append(entry)
    return unique


def load_existing_sidecar_entries(slug: str) -> dict[str, dict]:
    if not APP_SIDECAR_PATH.exists():
        return {}

    payload = load_json(APP_SIDECAR_PATH, default={"channels": {}})
    entries = payload.get("channels", {}).get(slug, {}).get("entries", [])
    result: dict[str, dict] = {}
    for entry in entries:
        title = entry.get("title", "")
        key = normalize_title(title)
        if not key:
            continue
        result[key] = {
            "title": title,
            "video_id": entry.get("videoId", ""),
            "url": entry.get("url", ""),
            "aliases": entry.get("aliases", []),
        }
    return result
