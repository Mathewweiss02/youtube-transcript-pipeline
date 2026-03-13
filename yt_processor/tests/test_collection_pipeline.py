import sys
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from yt_processor import collection_utils as cu
from yt_processor.normalize_raw_transcripts import normalize_raw_transcripts
from yt_processor.transcript_scanner import scan_manual_collection
from yt_processor.universal_chunker import chunk_transcripts
from yt_processor.universal_parallel_downloader import discover_existing_transcripts, download_video, resolve_output_dir


class CollectionPipelineTests(unittest.TestCase):
    def test_normalize_title_strips_numbering_and_suffix(self):
        value = "1. Optimize Your Workspace for Productivity, Focus & Creativity | Huberman Lab Essentials.en"
        self.assertEqual(
            cu.normalize_title(value),
            "optimize-your-workspace-for-productivity-focus-and-creativity-huberman-lab-essentials",
        )

    def test_extract_candidates_dedupes_numbered_toc_and_body_heading(self):
        content = """# Dummy Collection

## Table of Contents
- 1. Optimize Your Workspace for Productivity, Focus & Creativity | Huberman Lab Essentials

---

# Optimize Your Workspace for Productivity, Focus & Creativity | Huberman Lab Essentials

URL: https://www.youtube.com/watch?v=23t_ynq2tmk

---

Transcript body.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bundle.md"
            path.write_text(content, encoding="utf-8")
            candidates = cu.extract_candidates_from_bundle(path)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0]["title"],
            "Optimize Your Workspace for Productivity, Focus & Creativity | Huberman Lab Essentials",
        )
        self.assertEqual(candidates[0]["video_id"], "23t_ynq2tmk")

    def test_extract_candidates_handles_collapsed_anchor_lines(self):
        content = """# Muay Thai Pros

## Table of Contents
- Muay Thai Basics

---

## Muay Thai Basics### <a id="three"></a>3 Basic Feints for Beginners to Use in Muay Thai Sparringhttps://www.youtube.com/watch?v=zLkSGcUFdjk# 3 Basic Feints for Beginners to Use in Muay Thai Sparringhttps://www.youtube.com/watch?v=zLkSGcUFdjktranscript---### <a id="five"></a>5 Sparring Tips that Will Make You Better at Muay Thaihttps://www.youtube.com/watch?v=RTuNMVIdonE# 5 Sparring Tips that Will Make You Better at Muay Thaihttps://www.youtube.com/watch?v=RTuNMVIdonEtranscript
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bundle.md"
            path.write_text(content, encoding="utf-8")
            candidates = cu.extract_candidates_from_bundle(path, ignored_titles=["Muay Thai Basics"])

        by_id = {candidate["video_id"]: candidate for candidate in candidates}
        self.assertEqual(set(by_id), {"zLkSGcUFdjk", "RTuNMVIdonE"})
        self.assertEqual(
            by_id["zLkSGcUFdjk"]["title"],
            "3 Basic Feints for Beginners to Use in Muay Thai Sparring",
        )
        self.assertEqual(
            by_id["RTuNMVIdonE"]["title"],
            "5 Sparring Tips that Will Make You Better at Muay Thai",
        )

    def test_extract_candidates_handles_separator_then_video_heading(self):
        content = """
---

# How Semen Retention effects your Testosterone and Performance (TIER LIST)

URL: https://www.youtube.com/watch?v=ryk_jWUnLGw

---

Transcript body.
"""
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "bundle.md"
            path.write_text(content, encoding="utf-8")
            candidates = cu.extract_candidates_from_bundle(path)

        self.assertEqual(len(candidates), 1)
        self.assertEqual(
            candidates[0]["title"],
            "How Semen Retention effects your Testosterone and Performance (TIER LIST)",
        )
        self.assertEqual(candidates[0]["video_id"], "ryk_jWUnLGw")

    def test_unique_entries_by_video_dedupes_bundle_overlap(self):
        entries = [
            {
                "video_id": "abc123xyz89",
                "normalized_title": "same-video",
                "source_channel_key": "source-one",
                "bundle_file": "full.md",
            },
            {
                "video_id": "abc123xyz89",
                "normalized_title": "same-video",
                "source_channel_key": "source-one",
                "bundle_file": "topic.md",
            },
            {
                "video_id": "",
                "normalized_title": "title-only-video",
                "source_channel_key": "source-one",
                "bundle_file": "topic.md",
            },
            {
                "video_id": "",
                "normalized_title": "title-only-video",
                "source_channel_key": "source-one",
                "bundle_file": "other.md",
            },
        ]

        unique_entries = cu.unique_entries_by_video(entries)
        self.assertEqual(len(unique_entries), 2)

    def test_registry_marks_solar_as_manifest_disabled(self):
        registry = cu.load_collection_registry()
        solar = registry["Solar_Athlete"]
        self.assertEqual(solar["collection_type"], "multi_channel_curated")
        self.assertEqual(solar["scan_strategy"], "manifest")
        self.assertEqual(solar["update_strategy"], "disabled")

    def test_scan_manual_collection_marks_manual_mode(self):
        collection = {
            "display_name": "Manual Test",
            "collection_type": "manual_only",
            "scan_strategy": "manual",
            "update_strategy": "disabled",
            "source_channels": [],
            "manual_reason": "Custom workflow only.",
        }
        result = scan_manual_collection("Manual_Test", collection)
        self.assertEqual(result["scan_mode_used"], "manual")
        self.assertIn("Custom workflow only.", result["scan_notes"])

    def test_chunk_transcripts_builds_output_from_raw_dir(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            raw_dir = root / "Example_Raw"
            output_dir = root / "Example"
            raw_dir.mkdir()

            (raw_dir / "aaa111bbb22.md").write_text(
                "# First Video\n\n"
                "URL: https://www.youtube.com/watch?v=aaa111bbb22\n\n"
                "---\n\n"
                "First transcript body.\n",
                encoding="utf-8",
            )
            (raw_dir / "ccc333ddd44.md").write_text(
                "# Second Video\n\n"
                "URL: https://www.youtube.com/watch?v=ccc333ddd44\n\n"
                "---\n\n"
                "Second transcript body.\n",
                encoding="utf-8",
            )

            result = chunk_transcripts(
                input_dir=raw_dir,
                output_dir=output_dir,
                base_name="EXAMPLE",
                sort_mode="name",
                replace_existing=True,
            )

            self.assertEqual(result["section_count"], 2)
            self.assertEqual(len(result["written_paths"]), 1)
            written_content = result["written_paths"][0].read_text(encoding="utf-8")
            self.assertIn("# EXAMPLE - Part 01", written_content)
            self.assertIn("1. First Video", written_content)
            self.assertIn("2. Second Video", written_content)

    def test_discover_existing_transcripts_indexes_title_named_raw_file_by_url(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = Path(tmp_dir)
            (raw_dir / "Legacy Title Export.md").write_text(
                "# Legacy Title Export\n\n"
                "URL: https://www.youtube.com/watch?v=abc123xyz89\n\n"
                "---\n\n"
                "Transcript body.\n",
                encoding="utf-8",
            )

            existing = discover_existing_transcripts(raw_dir)
            self.assertEqual(existing["abc123xyz89"].name, "Legacy Title Export.md")

    def test_download_video_skips_when_matching_video_exists_under_legacy_filename(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            raw_dir = Path(tmp_dir)
            existing_path = raw_dir / "Old Hyperarch Export.md"
            existing_path.write_text(
                "# Old Hyperarch Export\n\n"
                "URL: https://www.youtube.com/watch?v=abc123xyz89\n\n"
                "---\n\n"
                "Transcript body.\n",
                encoding="utf-8",
            )

            existing = discover_existing_transcripts(raw_dir)
            title, status, message = download_video(
                ("Fresh Channel Title", "https://www.youtube.com/watch?v=abc123xyz89"),
                raw_dir,
                overwrite=False,
                existing_transcripts=existing,
            )

            self.assertEqual(title, "Fresh Channel Title")
            self.assertEqual(status, "SKIPPED")
            self.assertEqual(message, existing_path.name)

    def test_normalize_raw_transcripts_archives_duplicate_and_renames_unique_legacy_files(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            root = Path(tmp_dir)
            raw_dir = root / "Hyperarch_Fascia_Raw"
            archive_dir = root / "Hyperarch_Fascia_Raw_Legacy"
            raw_dir.mkdir()

            (raw_dir / "abc123xyz89.md").write_text(
                "# Canonical Export\n\n"
                "URL: https://www.youtube.com/watch?v=abc123xyz89\n\n"
                "---\n\n"
                "Canonical body.\n",
                encoding="utf-8",
            )
            duplicate_legacy = raw_dir / "Old Title.md"
            duplicate_legacy.write_text(
                "# Old Title\n\n"
                "URL: https://www.youtube.com/watch?v=abc123xyz89\n\n"
                "---\n\n"
                "Legacy body.\n",
                encoding="utf-8",
            )
            unique_legacy = raw_dir / "Unique Title.md"
            unique_legacy.write_text(
                "# Unique Title\n\n"
                "URL: https://www.youtube.com/watch?v=zzz999yyy88\n\n"
                "---\n\n"
                "Unique body.\n",
                encoding="utf-8",
            )

            summary = normalize_raw_transcripts(raw_dir, archive_dir, dry_run=False)

            self.assertEqual(summary["kept_canonical"], 1)
            self.assertEqual(summary["archived_duplicates"], 1)
            self.assertEqual(summary["renamed_to_canonical"], 1)
            self.assertFalse(duplicate_legacy.exists())
            self.assertTrue((archive_dir / "Old Title.md").exists())
            self.assertFalse(unique_legacy.exists())
            self.assertTrue((raw_dir / "zzz999yyy88.md").exists())

    def test_downloader_default_output_dir_uses_repo_transcripts_root(self):
        class Args:
            output_dir = None
            channel_url = "https://www.youtube.com/@ScottyOptimal"
            workspace = None

        resolved = resolve_output_dir(Args())
        self.assertEqual(resolved.name, "ScottyOptimal_Raw")
        self.assertEqual(resolved.parent.name, "transcripts")

    def test_configure_runtime_root_repoints_workspace_paths(self):
        original_root = cu.REPO_ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                workspace_root = Path(tmp_dir)
                cu.configure_runtime_root(workspace_root)
                self.assertEqual(cu.REPO_ROOT, workspace_root)
                self.assertEqual(cu.TRANSCRIPTS_ROOT, workspace_root / "transcripts")
                self.assertEqual(cu.PENDING_PATH, workspace_root / "yt_processor" / "pending_updates.json")
                self.assertEqual(cu.REPORTS_DIR, workspace_root / "yt_processor" / "reports")
        finally:
            cu.configure_runtime_root(original_root)

    def test_manifest_source_path_falls_back_to_bundled_manifest(self):
        original_root = cu.REPO_ROOT
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                cu.configure_runtime_root(Path(tmp_dir))
                registry = cu.load_collection_registry()
                solar = registry["Solar_Athlete"]
                manifest_path = cu.resolve_manifest_source_path(solar)
                self.assertTrue(manifest_path.exists())
                self.assertIn("yt_processor", str(manifest_path))
        finally:
            cu.configure_runtime_root(original_root)

    def test_build_collection_provenance_module_help_runs(self):
        result = subprocess.run(
            [sys.executable, "-m", "yt_processor.build_collection_provenance", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--workspace", result.stdout)


if __name__ == "__main__":
    unittest.main()
