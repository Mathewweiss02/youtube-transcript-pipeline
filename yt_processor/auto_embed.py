#!/usr/bin/env python3
"""
Automated transcript -> embedding pipeline runner.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import transcript_scanner
import transcript_updater
from cost_tracker import CostTracker
from wiki_pipeline import process_channel


SCRIPT_DIR = Path(__file__).resolve().parent
PIPELINE_LOG_PATH = SCRIPT_DIR / "pipeline_log.json"


def load_pipeline_log() -> Dict[str, List[Dict[str, Any]]]:
    if not PIPELINE_LOG_PATH.exists():
        return {"runs": []}

    with open(PIPELINE_LOG_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        return {"runs": []}

    runs = payload.get("runs", [])
    if not isinstance(runs, list):
        runs = []

    return {"runs": runs}


def save_pipeline_log(payload: Dict[str, Any]):
    with open(PIPELINE_LOG_PATH, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)


def append_pipeline_log(entry: Dict[str, Any]):
    payload = load_pipeline_log()
    payload["runs"].append(entry)
    save_pipeline_log(payload)


def run_pipeline(
    channel: str,
    dry_run: bool = False,
    daily_budget: Optional[float] = None,
    skip_pinecone: bool = False,
) -> Dict[str, Any]:
    """Run scan -> update -> cost check -> embed for a single channel."""
    started_at = datetime.now(timezone.utc)
    tracker = CostTracker()
    registry = transcript_scanner.load_registry()
    channels = registry.get("channels", {})

    if channel not in channels:
        raise ValueError(f"Channel '{channel}' not found in registry")

    config = channels[channel]
    transcript_dir = transcript_scanner.REPO_ROOT / config["transcript_dir"]
    chunk_pattern = config.get("chunk_pattern", "*.md")

    scan_result: Dict[str, Any] = {}
    update_result: Dict[str, Any] = {}
    pipeline_result: Optional[Dict[str, Any]] = None
    error = None

    try:
        pending = transcript_scanner.load_pending()

        scan_result = transcript_scanner.scan_channel(channel, config)
        pending["channels"][channel] = scan_result
        pending["last_scan"] = datetime.now(timezone.utc).isoformat()

        if not dry_run:
            transcript_scanner.save_pending(pending)

        update_result = transcript_updater.update_channel(
            channel,
            config,
            pending,
            dry_run=dry_run,
        )

        if not dry_run:
            transcript_updater.save_json(transcript_updater.PENDING_PATH, pending)

        cost_estimate = tracker.estimate_channel_cost(transcript_dir, chunk_pattern)
        within_budget = tracker.check_budget(cost_estimate["estimated_cost"], daily_budget)

        if dry_run:
            status = "dry_run"
        elif update_result.get("appended", 0) == 0:
            status = "no_changes"
        elif not within_budget:
            status = "budget_skipped"
        else:
            status = "success"
            pipeline_result = process_channel(
                channel,
                skip_pinecone=skip_pinecone,
                daily_budget=daily_budget,
            )

        summary = {
            "channel": channel,
            "status": status,
            "dry_run": dry_run,
            "daily_budget": daily_budget,
            "cost_estimate": cost_estimate,
            "within_budget": within_budget,
            "scan": {
                "new_count": scan_result.get("new_count", 0),
                "total_on_youtube": scan_result.get("total_on_youtube", 0),
                "total_transcribed": scan_result.get("total_transcribed", 0),
            },
            "update": update_result,
            "pipeline": pipeline_result,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        error = str(exc)
        summary = {
            "channel": channel,
            "status": "failed",
            "dry_run": dry_run,
            "daily_budget": daily_budget,
            "error": error,
            "scan": scan_result,
            "update": update_result,
            "pipeline": pipeline_result,
            "started_at": started_at.isoformat(),
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    append_pipeline_log(summary)

    if error:
        raise RuntimeError(error)

    return summary


def resolve_targets(channels: Dict[str, Any], requested: List[str], run_all: bool) -> List[str]:
    if run_all:
        return list(channels.keys())

    if not requested:
        raise ValueError("Provide a channel name or use --all")

    targets = []
    for name in requested:
        if name in channels:
            targets.append(name)
            continue

        match = next((key for key in channels if key.lower() == name.lower()), None)
        if not match:
            raise ValueError(f"Unknown channel '{name}'")
        targets.append(match)

    return targets


def main():
    parser = argparse.ArgumentParser(description="Run the auto-embed pipeline")
    parser.add_argument("channels", nargs="*", help="Channel name(s) from registry")
    parser.add_argument("--all", action="store_true", help="Run all channels")
    parser.add_argument("--dry-run", action="store_true", help="Run scan/update only")
    parser.add_argument("--daily-budget", type=float, default=None, help="Daily embedding budget in USD")
    parser.add_argument("--skip-pinecone", action="store_true", help="Skip Pinecone upload after embedding")
    args = parser.parse_args()

    registry = transcript_scanner.load_registry()
    channels = registry.get("channels", {})
    targets = resolve_targets(channels, args.channels, args.all)

    print("=" * 70)
    print("  AUTO EMBED PIPELINE")
    print(f"  Channels: {', '.join(targets)}")
    if args.dry_run:
        print("  Mode: dry run")
    if args.daily_budget is not None:
        print(f"  Daily budget: ${args.daily_budget:.4f}")
    print("=" * 70)

    results = []
    for channel in targets:
        results.append(
            run_pipeline(
                channel,
                dry_run=args.dry_run,
                daily_budget=args.daily_budget,
                skip_pinecone=args.skip_pinecone,
            )
        )

    print("\nSummary:")
    for result in results:
        print(
            f"  {result['channel']}: {result['status']} "
            f"(new={result.get('scan', {}).get('new_count', 0)}, "
            f"appended={result.get('update', {}).get('appended', 0)})"
        )


if __name__ == "__main__":
    main()
