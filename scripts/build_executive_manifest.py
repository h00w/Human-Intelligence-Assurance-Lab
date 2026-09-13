from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

from huggingface_hub import HfApi, batch_bucket_files, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

from hia.executive_assurance import executive_assurance_decision

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "executive_assurance_manifest.json"
DATASET_REPO = "h0000w/Human-Intelligence-Assurance-Lab"
BUCKET = "h0000w/Human-Intelligence-Assurance-Lab-storage"


def _download_json(filename: str, token: str) -> dict | None:
    try:
        path = hf_hub_download(
            repo_id=DATASET_REPO,
            repo_type="dataset",
            filename=filename,
            token=token,
        )
    except EntryNotFoundError:
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    token = os.environ["HF_TOKEN"]
    stability_payload = _download_json("runs/stability_study_latest.json", token)
    calibration = _download_json("runs/calibration_report.json", token)
    stability = stability_payload.get("stability") if stability_payload else None
    decision = executive_assurance_decision(
        stability=stability,
        calibration=calibration,
        require_semantic_calibration=False,
    )

    payload = {
        "schema_version": "1.4",
        "created_at": datetime.now(UTC).isoformat(),
        "decision": asdict(decision),
        "release_scope": "HIA-Bench repeated-run production canary",
        "candidate": {
            "model": stability_payload.get("model") if stability_payload else None,
            "provider": stability_payload.get("provider") if stability_payload else None,
            "generation": stability_payload.get("generation") if stability_payload else None,
        },
        "production_confidence": stability,
        "semantic_calibration": calibration,
        "semantic_policy": {
            "mode": "release-critical" if calibration and calibration.get("semantic_release_critical") else "shadow",
            "promotion_requires_independent_human_labels": True,
        },
        "evidence_locations": {
            "stability": "runs/stability_study_latest.json",
            "calibration": "runs/calibration_report.json",
            "semantic_shadow": "runs/semantic_shadow_latest.json",
            "human_review_queue": "runs/human_review_queue.csv",
        },
        "limitations": [
            "This manifest applies only to the evaluated benchmark, model, provider, policy, and generation settings.",
            "Hosted inference latency is environment-dependent and should be monitored continuously.",
            "Semantic judge evidence remains non-release-critical until independent human calibration passes.",
            "HIA-Bench is synthetic and is not a clinical validation or ground-truth emotion benchmark.",
        ],
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    api = HfApi(token=token)
    api.upload_file(
        path_or_fileobj=str(OUT),
        path_in_repo="runs/executive_assurance_manifest.json",
        repo_id=DATASET_REPO,
        repo_type="dataset",
    )
    batch_bucket_files(
        BUCKET,
        add=[(str(OUT), "runs/executive_assurance_manifest.json")],
        token=token,
    )
    print(json.dumps(payload["decision"], indent=2))


if __name__ == "__main__":
    main()
