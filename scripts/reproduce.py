"""Generate a Production AI Evidence Contract v1 reproduction bundle."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "evidence" / "reproduction-plan.json"
SCHEMA_PATH = ROOT / "evidence" / "production-ai-evidence-contract-v1.schema.json"
CONTRACT_SOURCE = (
    "https://raw.githubusercontent.com/h00w/model-quality-release-gate/main/"
    "evidence/production-ai-evidence-contract-v1.schema.json"
)
IGNORED_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "artifacts",
}


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_path(path: Path) -> str:
    if path.is_file():
        return sha256_file(path)
    digest = hashlib.sha256()
    for child in sorted(item for item in path.rglob("*") if item.is_file()):
        if any(part in IGNORED_PARTS for part in child.relative_to(path).parts):
            continue
        digest.update(child.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(sha256_file(child).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def run_capture(argv: list[str], cwd: Path | None = None) -> tuple[int, str]:
    try:
        process = subprocess.run(
            argv,
            cwd=str(cwd or ROOT),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        return process.returncode, process.stdout
    except FileNotFoundError as exc:
        return 127, f"command not found: {exc}\n"


def git_value(*args: str) -> str | None:
    code, output = run_capture(["git", *args])
    return output.strip() if code == 0 else None


def tool_version(command: list[str]) -> str | None:
    code, output = run_capture(command)
    if code != 0 or not output.strip():
        return None
    return output.strip().splitlines()[0]


def substitute(command: list[str]) -> list[str]:
    mapping = {"{python}": sys.executable, "{repo}": str(ROOT)}
    return [mapping.get(token, token) for token in command]


def main() -> int:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    commit = git_value("rev-parse", "HEAD")
    if not commit or len(commit) != 40:
        print("error: unresolved git HEAD", file=sys.stderr)
        return 2

    branch = git_value("rev-parse", "--abbrev-ref", "HEAD")
    dirty = bool(
        (git_value("status", "--porcelain", "--untracked-files=no") or "").strip()
    )
    run_id = (
        dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + commit[:12]
    )
    output_base = Path(
        os.environ.get("REPRO_OUT", str(ROOT / "artifacts" / "reproduction"))
    )
    if not output_base.is_absolute():
        output_base = ROOT / output_base
    output_dir = output_base / run_id
    logs_dir = output_dir / "logs"
    logs_dir.mkdir(parents=True, exist_ok=False)

    started_at = utc_now()
    steps: list[dict[str, Any]] = []
    all_passed = True

    for index, step in enumerate(plan["steps"], start=1):
        command = substitute(step["command"])
        step_start = time.monotonic()
        code, output = run_capture(command, ROOT / step.get("cwd", "."))
        duration = round(time.monotonic() - step_start, 6)
        safe_name = "".join(
            char if char.isalnum() or char in "-_" else "-" for char in step["name"]
        )
        log_relative = Path("logs") / f"{index:02d}-{safe_name}.log"
        (output_dir / log_relative).write_text(output, encoding="utf-8")
        passed = code == 0
        all_passed = all_passed and passed
        steps.append(
            {
                "name": step["name"],
                "command": command,
                "cwd": step.get("cwd", "."),
                "exit_code": code,
                "duration_seconds": duration,
                "passed": passed,
                "log": log_relative.as_posix(),
            }
        )
        if not passed and not step.get("continue_on_failure", False):
            break

    inputs: list[dict[str, str]] = []
    missing_inputs: list[str] = []
    for item in plan.get("inputs", []):
        path = ROOT / item["path"]
        if not path.exists():
            missing_inputs.append(item["path"])
            all_passed = False
            continue
        inputs.append(
            {
                "path": item["path"],
                "kind": item.get("kind", "input"),
                "sha256": sha256_path(path),
            }
        )

    if not all_passed:
        status = "FAILED"
        rationale = "One or more reproduction steps or declared inputs failed verification."
    elif dirty:
        status = "PARTIAL"
        rationale = (
            "All declared steps passed, but tracked working-tree changes were present."
        )
    else:
        status = "REPRODUCED"
        rationale = (
            "All declared deterministic reproduction steps passed from a clean tracked "
            "working tree."
        )

    finished_at = utc_now()
    summary_lines = [
        f"# Reproduction Summary — {plan['project']['name']}",
        "",
        "- Contract: Production AI Evidence Contract v1.0.0",
        f"- Commit: `{commit}`",
        f"- Branch: `{branch}`",
        f"- Dirty: `{str(dirty).lower()}`",
        f"- Status: **{status}**",
        "",
        "## Verification steps",
        "",
    ]
    for step in steps:
        marker = "PASS" if step["passed"] else "FAIL"
        summary_lines.append(
            f"- **{marker}** — `{step['name']}` — exit `{step['exit_code']}` — "
            f"{step['duration_seconds']:.3f}s"
        )
    summary_lines.extend(
        [
            "",
            "## Interpretation",
            "",
            rationale,
            "",
            "Reproduction status does not grant domain-specific production authorization.",
            "",
        ]
    )
    summary_path = output_dir / "summary.md"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    artifacts = []
    for path in sorted([summary_path, *logs_dir.glob("*.log")]):
        artifacts.append(
            {
                "path": path.relative_to(output_dir).as_posix(),
                "sha256": sha256_file(path),
                "media_type": "text/plain",
            }
        )

    notes = list(plan.get("notes", []))
    if missing_inputs:
        notes.append("Missing declared inputs: " + ", ".join(missing_inputs))
    notes.append("REPRODUCED is a reproduction status, not a deployment authorization.")

    evidence = {
        "contract_version": "1.0.0",
        "generated_at": finished_at,
        "contract_source": CONTRACT_SOURCE,
        "schema_sha256": sha256_file(SCHEMA_PATH),
        "repository": {
            "name": plan["project"]["repository_name"],
            "url": plan["project"]["repository_url"],
            "git_commit": commit,
            "branch": branch,
            "dirty": dirty,
        },
        "subject": {
            "name": plan["project"]["name"],
            "type": plan["project"]["subject_type"],
            "version": plan["project"].get("version", "git:" + commit[:12]),
            "candidate_id": plan["project"].get("candidate_id"),
        },
        "environment": {
            "os": platform.platform(),
            "architecture": platform.machine(),
            "python": sys.version.split()[0],
            "tools": {
                "git": tool_version(["git", "--version"]),
                "node": tool_version(["node", "--version"]),
                "npm": tool_version(["npm", "--version"]),
                "make": tool_version(["make", "--version"]),
            },
        },
        "inputs": inputs,
        "execution": {
            "started_at": started_at,
            "finished_at": finished_at,
            "steps": steps,
        },
        "decision": {
            "status": status,
            "rationale": rationale,
            "domain_decision": plan.get("domain_decision"),
            "domain_decision_source": plan.get("domain_decision_source"),
        },
        "artifacts": artifacts,
        "notes": notes,
    }
    evidence_path = output_dir / "evidence.json"
    evidence_path.write_text(
        json.dumps(evidence, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )

    checksum_targets = sorted([evidence_path, summary_path, *logs_dir.glob("*.log")])
    checksum_text = "".join(
        f"{sha256_file(path)}  {path.relative_to(output_dir).as_posix()}\n"
        for path in checksum_targets
    )
    (output_dir / "checksums.sha256").write_text(checksum_text, encoding="utf-8")
    (output_base / "LATEST").write_text(run_id + "\n", encoding="utf-8")

    print(f"evidence: {output_dir}")
    print(f"status: {status}")
    return 0 if status in {"REPRODUCED", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
