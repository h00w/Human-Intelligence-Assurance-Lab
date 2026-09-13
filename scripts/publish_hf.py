import os
from pathlib import Path

from huggingface_hub import HfApi, SpaceHardware

api = HfApi(token=os.environ["HF_TOKEN"])
owner = "h0000w"
base = "Human-Intelligence-Assurance-Lab"
root = Path(__file__).resolve().parents[1]
space_repo = f"{owner}/{base}"

# Dataset
api.upload_file(
    path_or_fileobj=str(root / "evals/scenarios/hia_bench_v0_1.jsonl"),
    path_in_repo="hia_bench_v0_1.jsonl",
    repo_id=f"{owner}/{base}",
    repo_type="dataset",
)
api.upload_file(
    path_or_fileobj=str(root / "publication/dataset/README.md"),
    path_in_repo="README.md",
    repo_id=f"{owner}/{base}",
    repo_type="dataset",
)

# Model/research artifact repo: evaluator/release-policy package, not model weights.
for local, remote in [
    ("publication/model/README.md", "README.md"),
    ("configs/release_policy.yaml", "release_policy.yaml"),
]:
    api.upload_file(
        path_or_fileobj=str(root / local),
        path_in_repo=remote,
        repo_id=f"{owner}/{base}",
    )

# Docker-based Streamlit Space. ZeroGPU is Gradio-only, so this deployment must run
# on CPU hardware. Model inference itself is remote through HF Inference Providers.
api.request_space_hardware(space_repo, hardware=SpaceHardware.CPU_BASIC)

space_files = {
    "app.py": "app.py",
    "requirements.txt": "requirements.txt",
    "Dockerfile": "Dockerfile",
    "publication/space/README.md": "README.md",
}
for local, remote in space_files.items():
    api.upload_file(
        path_or_fileobj=str(root / local),
        path_in_repo=remote,
        repo_id=space_repo,
        repo_type="space",
    )
api.upload_folder(
    folder_path=str(root / "hia"),
    path_in_repo="hia",
    repo_id=space_repo,
    repo_type="space",
)
api.upload_folder(
    folder_path=str(root / "evals"),
    path_in_repo="evals",
    repo_id=space_repo,
    repo_type="space",
)
print("Published HIA-Bench dataset, evaluator artifact repo, and CPU Basic Docker Space.")
