"""
Cost tracking utilities for embedding runs.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


EMBEDDING_MODEL = "text-embedding-3-small"
COST_PER_1M_TOKENS = 0.02
DEFAULT_LOG_PATH = Path(__file__).resolve().parent / "cost_log.json"


class CostTracker:
    """Estimate and track embedding spend."""

    def __init__(self, log_path: Optional[Path | str] = None):
        self.log_path = Path(log_path) if log_path else DEFAULT_LOG_PATH

    def estimate_channel_cost(
        self,
        transcript_dir: Path | str,
        chunk_pattern: str = "*.md",
    ) -> Dict[str, Any]:
        """Estimate embedding cost from transcript chunk files."""
        transcript_path = Path(transcript_dir)
        if not transcript_path.exists():
            return {
                "words": 0,
                "tokens": 0,
                "estimated_cost": 0.0,
                "file_count": 0,
            }

        files = sorted(transcript_path.glob(chunk_pattern))
        if not files:
            files = sorted(transcript_path.glob("*.md"))

        words = 0
        file_count = 0

        for file_path in files:
            if not file_path.is_file():
                continue
            if file_path.suffix.lower() != ".md":
                continue
            if file_path.stem.upper().startswith("INDEX"):
                continue

            text = file_path.read_text(encoding="utf-8", errors="ignore")
            words += len(re.findall(r"\S+", text))
            file_count += 1

        tokens = int(words * 1.3)
        estimated_cost = round((tokens / 1_000_000) * COST_PER_1M_TOKENS, 6)

        return {
            "words": words,
            "tokens": tokens,
            "estimated_cost": estimated_cost,
            "file_count": file_count,
        }

    def check_budget(self, estimated_cost: float, daily_budget: Optional[float]) -> bool:
        """Return True when the estimated spend fits within today's budget."""
        if daily_budget is None:
            return True

        today_spend = self.get_today_spend()
        return (today_spend["cost"] + estimated_cost) <= daily_budget

    def log_spend(
        self,
        channel: str,
        tokens: int,
        cost: float,
        model: str = EMBEDDING_MODEL,
    ) -> Dict[str, Any]:
        """Append a spend record to the log."""
        payload = self._load_log()
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "channel": channel,
            "tokens": int(tokens),
            "cost": round(float(cost), 6),
            "model": model,
        }
        payload["entries"].append(entry)
        self._save_log(payload)
        return entry

    def get_today_spend(self) -> Dict[str, Any]:
        """Summarize spend for the current UTC day."""
        payload = self._load_log()
        today = datetime.now(timezone.utc).date().isoformat()

        entries = [
            entry
            for entry in payload["entries"]
            if entry.get("timestamp", "").startswith(today)
        ]

        return {
            "date": today,
            "cost": round(sum(float(entry.get("cost", 0.0)) for entry in entries), 6),
            "tokens": sum(int(entry.get("tokens", 0)) for entry in entries),
            "entries": len(entries),
        }

    def get_monthly_report(self) -> Dict[str, Any]:
        """Aggregate spend by month."""
        payload = self._load_log()
        report: Dict[str, Dict[str, Any]] = {}

        for entry in payload["entries"]:
            timestamp = entry.get("timestamp", "")
            month = timestamp[:7] if len(timestamp) >= 7 else "unknown"
            channel = entry.get("channel", "unknown")
            month_bucket = report.setdefault(
                month,
                {"cost": 0.0, "tokens": 0, "entries": 0, "channels": {}},
            )

            month_bucket["cost"] += float(entry.get("cost", 0.0))
            month_bucket["tokens"] += int(entry.get("tokens", 0))
            month_bucket["entries"] += 1
            month_bucket["channels"][channel] = month_bucket["channels"].get(channel, 0.0) + float(
                entry.get("cost", 0.0)
            )

        for bucket in report.values():
            bucket["cost"] = round(bucket["cost"], 6)
            bucket["channels"] = {
                channel: round(cost, 6)
                for channel, cost in sorted(
                    bucket["channels"].items(),
                    key=lambda item: item[1],
                    reverse=True,
                )
            }

        return {
            "model": EMBEDDING_MODEL,
            "months": dict(sorted(report.items())),
        }

    def _load_log(self) -> Dict[str, List[Dict[str, Any]]]:
        if not self.log_path.exists():
            return {"entries": []}

        with open(self.log_path, "r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if not isinstance(payload, dict):
            return {"entries": []}

        entries = payload.get("entries", [])
        if not isinstance(entries, list):
            entries = []

        return {"entries": entries}

    def _save_log(self, payload: Dict[str, Any]):
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.log_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    tracker = CostTracker()
    print(json.dumps(tracker.get_monthly_report(), indent=2))
