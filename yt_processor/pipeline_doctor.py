#!/usr/bin/env python3
"""First-run environment checks for the public transcript pipeline repo."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from . import collection_utils as cu
    from .universal_chunker import chunk_transcripts
except ImportError:
    import collection_utils as cu
    from universal_chunker import chunk_transcripts


OPTIONAL_PACKAGES = ("openai", "pinecone", "tiktoken", "tenacity")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate a local setup for the transcript pipeline repo.")
    parser.add_argument(
        "--workspace",
        type=Path,
        help="Workspace root for transcript data, reports, and pending update files",
    )
    parser.add_argument(
        "--create-dirs",
        action="store_true",
        help="Create missing workspace directories such as transcripts/ for first-run setup",
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


def print_optional(label: str, installed: bool, detail: str):
    status = "OPTIONAL"
    suffix = "installed" if installed else "not installed"
    print(f"[{status}] {label}: {detail} ({suffix})")


def check_python() -> bool:
    version = sys.version_info
    ok = version >= (3, 10)
    detail = f"{version.major}.{version.minor}.{version.micro}"
    print_result("Python", ok, detail)
    return ok


def check_workspace_root(create_dirs: bool) -> bool:
    workspace_root = cu.REPO_ROOT
    runtime_dir = cu.REPORTS_DIR.parent
    if create_dirs:
        runtime_dir.mkdir(parents=True, exist_ok=True)
    ok = workspace_root.exists() and runtime_dir.exists()
    print_result("Workspace", ok, str(workspace_root))
    return ok


def check_transcripts_dir(create_dirs: bool) -> bool:
    transcripts_dir = cu.TRANSCRIPTS_ROOT
    if create_dirs:
        transcripts_dir.mkdir(parents=True, exist_ok=True)
    ok = transcripts_dir.exists()
    print_result("Workspace transcripts dir", ok, str(transcripts_dir))
    return ok


def check_yt_dlp() -> bool:
    try:
        package_version = importlib.metadata.version("yt-dlp")
    except importlib.metadata.PackageNotFoundError:
        package_version = None

    try:
        result = subprocess.run(
            cu.get_yt_dlp_command("--version"),
            capture_output=True,
            text=True,
            timeout=15,
            check=True,
        )
    except Exception as exc:
        detail = cu.describe_yt_dlp_command()
        if package_version:
            detail += f" [package {package_version}]"
        print_result("yt-dlp", False, f"{detail} ({exc})")
        return False

    version = (result.stdout or result.stderr or "").strip().splitlines()[:1]
    detail = cu.describe_yt_dlp_command()
    if version:
        detail += f" ({version[0]})"
    if package_version:
        detail += f" [package {package_version}]"
    print_result("yt-dlp", True, detail)
    return True


def check_write_permissions(create_dirs: bool) -> bool:
    probe_dir = cu.REPORTS_DIR.parent
    if create_dirs:
        probe_dir.mkdir(parents=True, exist_ok=True)

    try:
        probe_dir.mkdir(parents=True, exist_ok=True)
        probe = probe_dir / ".doctor_write_probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
    except OSError as exc:
        print_result("Write access", False, f"{probe_dir} ({exc})")
        return False

    print_result("Write access", True, str(probe_dir))
    return True


def check_optional_packages():
    for package in OPTIONAL_PACKAGES:
        try:
            importlib.import_module(package)
            print_optional(f"Optional package `{package}`", True, package)
        except Exception:
            print_optional(f"Optional package `{package}`", False, package)


def verify_examples() -> bool:
    sample_raw_dir = cu.get_examples_root() / "sample_raw"
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


def main() -> int:
    args = parse_args()
    cu.configure_runtime_root(args.workspace)
    checks = [
        check_python(),
        check_workspace_root(create_dirs=args.create_dirs),
        check_transcripts_dir(create_dirs=args.create_dirs),
        check_write_permissions(create_dirs=args.create_dirs),
        check_yt_dlp(),
    ]

    check_optional_packages()

    if args.verify_examples:
        checks.append(verify_examples())

    print()
    if all(checks):
        print("Pipeline doctor passed.")
        print("Next step: run yt-pipeline-download --channel-url https://www.youtube.com/@ChannelHandle")
        return 0

    print("Pipeline doctor found setup issues.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
