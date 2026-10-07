"""Upload the dataset files + card to the Hugging Face Hub (maintainer helper, not used by judges).

Usage: python scripts/upload_hf.py --repo USER/swisscivicqa-4l [--private]
Reads HF_TOKEN from ~/.config/hack-apertus/env. Requires `pip install huggingface_hub`.
"""
import argparse
import os
import shutil
import tempfile
from pathlib import Path

from huggingface_hub import HfApi

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "README.md": "data/hf/README.md",
    "eval.jsonl": "data/dataset/eval.jsonl",
    "metadata.jsonl": "data/dataset/metadata.jsonl",
    "human_review.jsonl": "data/human_review/review.jsonl",
}


def token() -> str:
    for line in open(os.path.expanduser("~/.config/hack-apertus/env"), encoding="utf-8"):
        if line.startswith("HF_TOKEN="):
            return line.split("=", 1)[1].strip()
    raise SystemExit("HF_TOKEN not found")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--private", action="store_true")
    args = ap.parse_args()
    api = HfApi(token=token())
    api.create_repo(args.repo, repo_type="dataset", private=args.private, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for dst, src in FILES.items():
            shutil.copy(ROOT / src, Path(tmp) / dst)
        for p in (ROOT / "data" / "results").glob("*.jsonl"):
            shutil.copy(p, Path(tmp) / p.name)
        api.upload_folder(folder_path=tmp, repo_id=args.repo, repo_type="dataset",
                          commit_message="SwissCivicQA-4L v1.0")
    print(f"https://huggingface.co/datasets/{args.repo}")


if __name__ == "__main__":
    main()
