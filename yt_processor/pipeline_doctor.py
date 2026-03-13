#!/usr/bin/env python3
"""First-run environment checks for the public transcript pipeline repo."""

from __future__ import annotations

import argparse
import importlib
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from collection_utils import REPO_ROOT, YT_DLP_PATH
from universal_chunker import chunk_transcripts


OPTIONAL_PACKAGES = ("openai", "pinecone", "tiktoken", "tenacity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a local setup for the transcript pipeline repo.")
    parser.add_argument(
        "--create-dirs",
        action="store_true",
        help="Create missing repo directories such as transcripts/ for first-run setup",
    )
    parser.add_argument(
        "--verify-examples",
        action="store_true",
        help="Run a tiny chunking check against examples/sample_raw",
    )
    return parser.parse_args()


def print_result(label: str, ok: bool, detail: str):
    status = "OK" if ok else "FAIL"
    print(f"[{status}] {label}: {detail}")


def check_python() -> bool:
    version = sys.version_info
    ok = version >= (3, 10)
    detail = f"{version.major}.{version.minor}.{version.micro}"
    print_result("Python", ok, detail)
    return ok


def check_repo_dirs(create_dirs: bool) -> bool:
    transcripts_dir = REPO_ROOT / "transcripts"
    if not transcripts_dir.exists() and create_dirs:
        transcripts_dir.mkdir(parents=True, exist_ok=True)
    ok = transcripts_dir.exists()
    print_result("Repo transcripts dir", ok, str(transcripts_dir))
    return ok


def check_yt_dlp() -> bool:
    try:
        result = subprocess.run(
            [YT_DLP_PATH, "--version"],
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except Exception as exc:
        print_result("yt-dlp", False, f"{YT_DLP_PATH} ({exc})")
        return False

    version = (result.stdout or result.stderr or "").strip().splitlines()[:1]
    print_result("yt-dlp", True, f"{YT_DLP_PATH} ({version[0] if version else 'version unknown'})")
    return True


def check_optional_packages():
    for package in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(package)
            print_result(f"Optional package `{package}`", True, "installed")
        except Exception:
            print_result(f"Optional package `{package}`", False, "not installed")


def verify_examples() -> bool:
    sample_raw_dir = REPO_ROOT / "examples" / "sample_raw"
    if not sample_raw_dir.exists():
        print_result("Example chunking", False, f"missing {sample_raw_dir}")
        return False

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_dir = Path(tmp_dir) / "Example"
        result = chunk_transcripts(
            input_dir=sample_raw_dir,
            output_dir=output_dir,
            base_name="EXAMPLE",
            sort_mode="name",
            replace_existing=True,
        )
        ok = len(result["written_paths"]) == 1 and result["section_count"] == 2
        detail = f"{result['section_count']} sections, {len(result['written_paths'])} chunk file(s)"
        print_result("Example chunking", ok, detail)
        return ok


def main():
    args = parse_args()
    checks = [
        check_python(),
        check_repo_dirs(create_dirs=args.create_dirs),
        check_yt_dlp(),
    ]

    check_optional_packages()

    if args.verify_examples:
        checks.append(verify_examples())

    print()
    if all(checks):
        print("Pipeline doctor passed.")
        print("Next step: run universal_parallel_downloader.py with --channel-url.")
        raise SystemExit(0)

    print("Pipeline doctor found setup issues.")
    raise SystemExit(1)


if __name__ == "__main__":
    main()
