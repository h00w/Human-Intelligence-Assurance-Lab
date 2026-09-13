from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

from hia.v1_readiness import assess_v1_readiness

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "phase_1_v1_readiness.json"
DATASET = "h0000w/Human-Intelligence-Assurance-Lab"


def load_dataset_json(path: str, token: str | None):
    try:
        local = hf_hub_download(DATASET, path, repo_type="dataset", token=token)
        return json.loads(Path(local).read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> None:
    token = os.getenv("HF_TOKEN")
    adaptive = load_dataset_json("runs/adaptive_hedging_latest.json", token)
    calibration = load_dataset_json("runs/calibration_report.json", token)
    long_window = load_dataset_json("runs/long_window_latest.json", token)
    dedicated = load_dataset_json("runs/dedicated_qualification_latest.json", token)

    result = assess_v1_readiness(
        phase18_ship=bool(adaptive and adaptive.get("executive_decision", {}).get("decision") == "SHIP"),
        human_calibrated=bool(calibration and calibration.get("semantic_release_critical") is True),
        long_window_ready=bool(long_window and long_window.get("report", {}).get("ready") is True),
        dedicated_status=(dedicated or {}).get("status", "NOT_CONFIGURED"),
    )
    payload = {
        "schema_version": "1.0",
        "phase": "Phase 1",
        "target_release": "v1.0.0",
        "readiness": asdict(result),
        "evidence": {
            "phase_1_8": "runs/adaptive_hedging_latest.json" if adaptive else None,
            "human_calibration": "runs/calibration_report.json" if calibration else None,
            "long_window": "runs/long_window_latest.json" if long_window else None,
            "dedicated": "runs/dedicated_qualification_latest.json" if dedicated else None,
        },
        "release_rule": "READY only when all maturity gates pass; missing evidence is BLOCKED, failed required evidence is HOLD.",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))

    if token:
        HfApi(token=token).upload_file(
            path_or_fileobj=str(OUT),
            path_in_repo="runs/phase_1_v1_readiness.json",
            repo_id=DATASET,
            repo_type="dataset",
        )


if __name__ == "__main__":
    main()
