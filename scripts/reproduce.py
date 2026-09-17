#!/usr/bin/env python3
from __future__ import annotations
import datetime as dt, hashlib, json, os, platform, subprocess, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]; PLAN=ROOT/"evidence"/"reproduction-plan.json"; SCHEMA=ROOT/"evidence"/"production-ai-evidence-contract-v1.schema.json"
SOURCE="https://raw.githubusercontent.com/h00w/model-quality-release-gate/main/evidence/production-ai-evidence-contract-v1.schema.json"; IGNORED={".git",".venv","node_modules","__pycache__",".pytest_cache","artifacts"}
def now(): return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00","Z")
def hfile(p):
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
 return h.hexdigest()
def hpath(p):
 if p.is_file(): return hfile(p)
 h=hashlib.sha256()
 for f in sorted(x for x in p.rglob("*") if x.is_file()):
  if any(part in IGNORED for part in f.relative_to(p).parts): continue
  h.update(f.relative_to(ROOT).as_posix().encode()); h.update(b"\0"); h.update(hfile(f).encode()); h.update(b"\n")
 return h.hexdigest()
def run(argv,cwd=None):
 try:
  p=subprocess.run(argv,cwd=str(cwd or ROOT),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=False); return p.returncode,p.stdout
 except FileNotFoundError as e: return 127,f"command not found: {e}\n"
def git(*a):
 c,o=run(["git",*a]); return o.strip() if c==0 else None
def ver(c):
 rc,o=run(c); return o.strip().splitlines()[0] if rc==0 and o.strip() else None
def main():
 plan=json.loads(PLAN.read_text()); commit=git("rev-parse","HEAD")
 if not commit or len(commit)!=40: print("error: unresolved git HEAD",file=sys.stderr); return 2
 branch=git("rev-parse","--abbrev-ref","HEAD"); dirty=bool((git("status","--porcelain","--untracked-files=no") or "").strip())
 rid=dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+commit[:12]; base=Path(os.environ.get("REPRO_OUT",ROOT/"artifacts"/"reproduction")); base=base if base.is_absolute() else ROOT/base; out=base/rid; logs=out/"logs"; logs.mkdir(parents=True,exist_ok=False)
 start=now(); steps=[]; ok=True
 for i,s in enumerate(plan["steps"],1):
  argv=[sys.executable if x=="{python}" else str(ROOT) if x=="{repo}" else x for x in s["command"]]; t=time.monotonic(); code,text=run(argv,ROOT/s.get("cwd",".")); dur=round(time.monotonic()-t,6); name="".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in s["name"]); rel=Path("logs")/f"{i:02d}-{name}.log"; (out/rel).write_text(text,encoding="utf-8"); passed=code==0; ok=ok and passed; steps.append({"name":s["name"],"command":argv,"cwd":s.get("cwd","."),"exit_code":code,"duration_seconds":dur,"passed":passed,"log":rel.as_posix()})
  if not passed and not s.get("continue_on_failure",False): break
 inputs=[]; missing=[]
 for x in plan.get("inputs",[]):
  p=ROOT/x["path"]
  if not p.exists(): missing.append(x["path"]); ok=False; continue
  inputs.append({"path":x["path"],"kind":x.get("kind","input"),"sha256":hpath(p)})
 status="FAILED" if not ok else "PARTIAL" if dirty else "REPRODUCED"; rationale={"FAILED":"One or more reproduction steps or declared inputs failed verification.","PARTIAL":"All declared steps passed, but tracked working-tree changes were present.","REPRODUCED":"All declared deterministic reproduction steps passed from a clean tracked working tree."}[status]; finish=now()
 summary=[f"# Reproduction Summary — {plan['project']['name']}","",f"- Contract: Production AI Evidence Contract v1.0.0",f"- Commit: `{commit}`",f"- Branch: `{branch}`",f"- Dirty: `{str(dirty).lower()}`",f"- Status: **{status}**","","## Verification steps",""]+[f"- **{'PASS' if s['passed'] else 'FAIL'}** — `{s['name']}` — exit `{s['exit_code']}` — {s['duration_seconds']:.3f}s" for s in steps]+["","## Interpretation","",rationale,"","Reproduction status does not grant domain-specific production authorization.",""]; sp=out/"summary.md"; sp.write_text("\n".join(summary),encoding="utf-8")
 arts=[{"path":p.relative_to(out).as_posix(),"sha256":hfile(p),"media_type":"text/plain"} for p in sorted([sp,*logs.glob("*.log")])]
 ev={"contract_version":"1.0.0","generated_at":finish,"contract_source":SOURCE,"schema_sha256":hfile(SCHEMA),"repository":{"name":plan["project"]["repository_name"],"url":plan["project"]["repository_url"],"git_commit":commit,"branch":branch,"dirty":dirty},"subject":{"name":plan["project"]["name"],"type":plan["project"]["subject_type"],"version":plan["project"].get("version","git:"+commit[:12]),"candidate_id":plan["project"].get("candidate_id")},"environment":{"os":platform.platform(),"architecture":platform.machine(),"python":sys.version.split()[0],"tools":{"git":ver(["git","--version"]),"node":ver(["node","--version"]),"npm":ver(["npm","--version"]),"make":ver(["make","--version"])}},"inputs":inputs,"execution":{"started_at":start,"finished_at":finish,"steps":steps},"decision":{"status":status,"rationale":rationale,"domain_decision":plan.get("domain_decision"),"domain_decision_source":plan.get("domain_decision_source")},"artifacts":arts,"notes":list(plan.get("notes",[]))+((["Missing declared inputs: "+", ".join(missing)]) if missing else [])+["REPRODUCED is a reproduction status, not a deployment authorization."]}; ep=out/"evidence.json"; ep.write_text(json.dumps(ev,indent=2,sort_keys=True)+"\n",encoding="utf-8"); targets=sorted([ep,sp,*logs.glob("*.log")]); (out/"checksums.sha256").write_text("".join(f"{hfile(p)}  {p.relative_to(out).as_posix()}\n" for p in targets),encoding="utf-8"); (base/"LATEST").write_text(rid+"\n"); print(f"evidence: {out}\nstatus: {status}"); return 0 if status in {"REPRODUCED","PARTIAL"} else 1
if __name__=="__main__": raise SystemExit(main())
