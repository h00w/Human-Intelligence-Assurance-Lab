from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from hia.authoritative import PHASE_1_8_AUTHORITATIVE
from hia.v1_readiness import assess_v1_readiness

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "phase_1_v1_readiness.json"
DATASET = "h0000w/Human-Intelligence-Assurance-Lab"


def load_dataset_json(path: str, token: str | None):
    try:
        local = hf_hub_download(DATASET, path, repo_type="dataset", token=token)
        return json.loads(Path(local).read_text(encoding="utf-8"))
    except (HfHubHTTPError, OSError, json.JSONDecodeError):
        return None


def main() -> None:
    token = os.getenv("HF_TOKEN")
    operational_adaptive = load_dataset_json("runs/adaptive_hedging_latest.json", token)
    calibration = load_dataset_json("runs/calibration_report.json", token)
    long_window = load_dataset_json("runs/long_window_latest.json", token)
    dedicated = load_dataset_json("runs/dedicated_qualification_latest.json", token)

    result = assess_v1_readiness(
        phase18_ship=PHASE_1_8_AUTHORITATIVE["decision"] == "SHIP",
        human_calibrated=bool(calibration and calibration.get("semantic_release_critical") is True),
        long_window_ready=bool(long_window and long_window.get("report", {}).get("ready") is True),
        dedicated_status=(dedicated or {}).get("status", "NOT_CONFIGURED"),
    )
    payload = {
        "schema_version": "1.1",
        "phase": "Phase 1",
        "target_release": "v1.0.0",
        "readiness": asdict(result),
        "authoritative_phase_1_8": PHASE_1_8_AUTHORITATIVE,
        "operational_latest": {
            "adaptive_executive_decision": (
                operational_adaptive.get("executive_decision", {}).get("decision")
                if operational_adaptive
                else None
            ),
            "long_window_status": (long_window or {}).get("status"),
        },
        "evidence": {
            "phase_1_8_authoritative_workflow_run": PHASE_1_8_AUTHORITATIVE["workflow_run_id"],
            "adaptive_operational_latest": "runs/adaptive_hedging_latest.json" if operational_adaptive else None,
            "human_calibration": "runs/calibration_report.json" if calibration else None,
            "long_window": "runs/long_window_latest.json" if long_window else None,
            "dedicated": "runs/dedicated_qualification_latest.json" if dedicated else None,
        },
        "release_rule": "The frozen Phase 1.8 release remains historical SHIP evidence; v1.0 additionally requires current human, longitudinal, and dedicated-infrastructure maturity gates.",
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
