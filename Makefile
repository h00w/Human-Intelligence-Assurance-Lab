.PHONY: reproduce reproduce-clean proof proof-offline proof-clean proof-package proof-verify deployment-contract-selftest deployment-template-check deployment-evidence-check

PYTHON ?= python

reproduce:
	$(PYTHON) scripts/reproduce.py

reproduce-clean:
	rm -rf evidence/out

proof: reproduce
	$(PYTHON) scripts/proof_level.py

proof-offline: reproduce
	$(PYTHON) scripts/proof_level.py --offline

proof-clean:
	rm -rf evidence/out

proof-package: proof
	python scripts/build_proof_bundle.py

proof-verify:
	python scripts/verify_proof_bundle.py

deployment-contract-selftest:
	python scripts/deployment_evidence_selftest.py

deployment-template-check:
	python scripts/validate_deployment_evidence.py evidence/deployment-evidence.example.json --minimum-observation-seconds 86400 --expect-not-qualified

deployment-evidence-check:
	python scripts/validate_deployment_evidence.py evidence/deployment-evidence.json --expected-commit "$$(git rev-parse HEAD)" --minimum-observation-seconds 86400
