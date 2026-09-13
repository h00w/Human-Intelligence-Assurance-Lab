from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from hia.drift import QualificationSnapshot, assess_long_window

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "artifacts" / "adaptive_hedging_latest.json"
OUT = ROOT / "artifacts" / "long_window_report.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
PREFIX = "runs/long_window/"


def snapshot_from_payload(payload: dict, timestamp: datetime) -> QualificationSnapshot:
    adaptive = payload["comparison"]["adaptive"]["report"]
    run = adaptive["run"]
    release = adaptive["release_report"]
    economics = payload["comparison"]["adaptive"]["economics"]
    return QualificationSnapshot(
        timestamp=timestamp,
        production_decision=adaptive["production_decision"]["decision"],
        mean_latency_ms=float(run["mean_latency_ms"] or 0),
        p95_latency_ms=float(run["p95_latency_ms"] or 0),
        blocker_failures=int(release["blocker_failures"]),
        provider_errors=int(run["provider_errors"]),
        truncations=int(run["completion_truncations"]),
        redundant_cost_rate=economics.get("redundant_cost_rate"),
    )


def main() -> None:
    if not SOURCE.exists():
        raise SystemExit("adaptive evidence missing; run scripts/run_adaptive_hedging.py first")
    token = os.getenv("HF_TOKEN")
    now = datetime.now(timezone.utc)
    current_payload = json.loads(SOURCE.read_text(encoding="utf-8"))
    current = snapshot_from_payload(current_payload, now)
    snapshots = [current]

    api = HfApi(token=token)
    if token:
        for path in api.list_repo_files(DATASET_REPO, repo_type="dataset"):
            if not path.startswith(PREFIX) or not path.endswith(".json"):
                continue
            try:
                local = hf_hub_download(DATASET_REPO, path, repo_type="dataset", token=token)
                prior = json.loads(Path(local).read_text(encoding="utf-8"))
                timestamp = datetime.fromisoformat(prior["timestamp"].replace("Z", "+00:00"))
                snapshots.append(snapshot_from_payload(prior["adaptive_payload"], timestamp))
            except (KeyError, ValueError, json.JSONDecodeError):
                continue

    report = assess_long_window(snapshots)
    payload = {
        "schema_version": "1.0",
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "status": report.status,
        "report": asdict(report),
        "adaptive_payload": current_payload,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    if token:
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        api.upload_file(
            path_or_fileobj=str(OUT),
            path_in_repo=f"{PREFIX}{stamp}.json",
            repo_id=DATASET_REPO,
            repo_type="dataset",
        )
        api.upload_file(
            path_or_fileobj=str(OUT),
            path_in_repo="runs/long_window_latest.json",
            repo_id=DATASET_REPO,
            repo_type="dataset",
        )
    print(json.dumps({"status": report.status, "report": asdict(report)}, indent=2))
    if report.status == "HOLD":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
