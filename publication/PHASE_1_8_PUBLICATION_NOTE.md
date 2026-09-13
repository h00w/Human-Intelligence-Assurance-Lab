# Phase 1.8 Publication Note

Phase 1.8 is the current authoritative routing qualification for Human Intelligence Assurance Lab.

- Executive verdict: **SHIP**
- Evidence: `runs/adaptive_hedging_latest.json`
- Result narrative: `docs/PHASE_1_8_RESULT.md`
- Dashboard: `pages/5_Adaptive_Hedging.py`
- Adaptive hedge delays are derived from measured primary-route latency and scenario risk.
- Cost/token duplication is reported separately from release eligibility.
- Repeated critical primary-timeout recovery passed 3/3 trials.
- Dedicated endpoint remains `NOT_CONFIGURED` and is not release-critical.

The initial Phase 1.8 HOLD caused by a real fallback `ReadTimeout` is superseded by the hardened Phase 1.8.1 qualification but retained as engineering history.
