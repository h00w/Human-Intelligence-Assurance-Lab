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
ADAPTIVE_LATEST = "runs/adaptive_hedging_latest.json"
DEFAULT_EPOCH = "critical-reserve-v1"


def snapshot_from_payload(payload: dict, timestamp: datetime) -> QualificationSnapshot:
    """Convert one full adaptive qualification into one longitudinal snapshot.

    The longitudinal decision follows the executive verdict, not merely the healthy
    adaptive sub-run. Critical fault-recovery failures therefore remain visible.
    """
    adaptive = payload["comparison"]["adaptive"]["report"]
    run = adaptive["run"]
    release = adaptive["release_report"]
    economics = payload["comparison"]["adaptive"]["economics"]
    fault_trials = payload.get("critical_fault_recovery", {}).get("trials", [])

    blocker_failures = int(release["blocker_failures"])
    provider_errors = int(run["provider_errors"])
    truncations = int(run["completion_truncations"])
    for item in fault_trials:
        report = item.get("report", item)
        blocker_failures += int(report.get("release_report", {}).get("blocker_failures", 0))
        provider_errors += int(report.get("run", {}).get("provider_errors", 0))
        truncations += int(report.get("run", {}).get("completion_truncations", 0))

    return QualificationSnapshot(
        timestamp=timestamp,
        production_decision=payload["executive_decision"]["decision"],
        mean_latency_ms=float(run["mean_latency_ms"] or 0),
        p95_latency_ms=float(run["p95_latency_ms"] or 0),
        blocker_failures=blocker_failures,
        provider_errors=provider_errors,
        truncations=truncations,
        redundant_cost_rate=economics.get("redundant_cost_rate"),
    )


def load_current_payload(token: str | None) -> dict:
    if SOURCE.exists():
        return json.loads(SOURCE.read_text(encoding="utf-8"))
    local = hf_hub_download(DATASET_REPO, ADAPTIVE_LATEST, repo_type="dataset", token=token)
    return json.loads(Path(local).read_text(encoding="utf-8"))


def main() -> None:
    token = os.getenv("HF_TOKEN")
    now = datetime.now(timezone.utc)
    current_payload = load_current_payload(token)
    epoch = current_payload.get("qualification_epoch", os.getenv("HIA_QUALIFICATION_EPOCH", DEFAULT_EPOCH))
    prefix = f"runs/long_window/{epoch}/"
    current = snapshot_from_payload(current_payload, now)
    snapshots = [current]

    api = HfApi(token=token)
    if token:
        for path in api.list_repo_files(DATASET_REPO, repo_type="dataset"):
            if not path.startswith(prefix) or not path.endswith(".json"):
                continue
            try:
                local = hf_hub_download(DATASET_REPO, path, repo_type="dataset", token=token)
                prior = json.loads(Path(local).read_text(encoding="utf-8"))
                if prior.get("qualification_epoch") != epoch:
                    continue
                timestamp = datetime.fromisoformat(prior["timestamp"].replace("Z", "+00:00"))
                snapshots.append(snapshot_from_payload(prior["adaptive_payload"], timestamp))
            except (KeyError, ValueError, json.JSONDecodeError):
                continue

    report = assess_long_window(snapshots)
    payload = {
        "schema_version": "1.2",
        "qualification_epoch": epoch,
        "timestamp": now.isoformat().replace("+00:00", "Z"),
        "status": report.status,
        "report": asdict(report),
        "current_snapshot": asdict(current),
        "adaptive_payload": current_payload,
        "note": (
            "Long-window status follows the full adaptive executive verdict, including repeated "
            "critical fault recovery, and only aggregates snapshots from the same qualification epoch."
        ),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")

    if token:
        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        for remote in (f"{prefix}{stamp}.json", "runs/long_window_latest.json"):
            api.upload_file(
                path_or_fileobj=str(OUT),
                path_in_repo=remote,
                repo_id=DATASET_REPO,
                repo_type="dataset",
            )
    print(
        json.dumps(
            {
                "qualification_epoch": epoch,
                "status": report.status,
                "report": asdict(report),
            },
            indent=2,
        )
    )
    if report.status == "HOLD":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
