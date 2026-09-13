from __future__ import annotations

import json
import os
from pathlib import Path

from hia.adapters.dedicated import DedicatedEndpointAdapter
from hia.model_eval import run_model_evaluation, select_canary
from hia.policy import risk_aware_system_prompt
from hia.runner import load_scenarios

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "dedicated_qualification_latest.json"


def main() -> None:
    endpoint = os.getenv("HIA_DEDICATED_ENDPOINT", "").strip()
    api_key = os.getenv("HIA_DEDICATED_API_KEY", "").strip()
    model = os.getenv("HIA_DEDICATED_MODEL", "meta-llama/Llama-3.1-8B-Instruct")

    if not endpoint or not api_key:
        payload = {
            "schema_version": "1.0",
            "status": "NOT_CONFIGURED",
            "release_critical": False,
            "provisioning_performed": False,
            "note": "No dedicated endpoint or credential was supplied; no billable infrastructure was created or contacted.",
        }
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps(payload, indent=2))
        return

    scenarios = select_canary(load_scenarios(), per_domain=2)
    report = run_model_evaluation(
        DedicatedEndpointAdapter(
            endpoint_url=endpoint,
            api_key=api_key,
            model=model,
            timeout_s=8.0,
        ),
        scenarios,
        system_prompt_builder=risk_aware_system_prompt,
    )
    run = report["run"]
    release = report["release_report"]
    production = report["production_decision"]
    qualified = (
        release["decision"] == "SHIP"
        and production["decision"] == "SHIP"
        and release["blocker_failures"] == 0
        and run["provider_errors"] == 0
        and run["completion_truncations"] == 0
        and (run["mean_latency_ms"] or 999999) <= 5000
        and (run["p95_latency_ms"] or 999999) <= 8000
    )
    payload = {
        "schema_version": "1.0",
        "status": "QUALIFIED" if qualified else "HOLD",
        "release_critical": True,
        "provisioning_performed": False,
        "report": report,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({"status": payload["status"], "run": run}, indent=2))
    if not qualified:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
