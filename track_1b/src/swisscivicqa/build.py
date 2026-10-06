"""Expand the fact source files into the per-language evaluation dataset.

Writes data/dataset/eval.jsonl (test cases) and data/dataset/metadata.jsonl
(instance-level provenance and licensing), one row per fact x language.

Usage: python -m swisscivicqa.build
"""
import hashlib
import json
from pathlib import Path

from .validate import LANGS, check, load_facts

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "dataset"
VERSION = "20240303"
FEDLEX = "https://www.fedlex.admin.ch/eli/cc/1999/404/{date}/{lang}"
LANG_NAMES = {"de": "German", "fr": "French", "it": "Italian", "rm": "Romansh (Rumantsch Grischun)"}
LICENSE_NOTE = (
    "Ground truth derived from the official text of the Federal Constitution (SR 101), "
    "which is not protected by copyright (Art. 5 para. 1 lit. a Swiss Copyright Act, URG). "
    "Questions and answer formulations are original work released under CDLA-Permissive-2.0."
)


def citation(fact: dict) -> str:
    art = fact["art"].replace("_", "")
    para = f" para. {fact['para']}" if fact["para"] else ""
    return f"Art. {art}{para} Cst. (SR 101)"


def main() -> None:
    facts = load_facts()
    errors = check(facts)
    if errors:
        raise SystemExit(f"{len(errors)} validation errors, run swisscivicqa.validate")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, meta = [], []
    for fact in facts:
        for lang in LANGS:
            item_id = f"{fact['id']}-{lang}"
            rows.append({
                "id": item_id,
                "fact_id": fact["id"],
                "language": lang,
                "question": fact["q"][lang],
                "gold_answer": fact["a"][lang][0],
                "gold_aliases": fact["a"][lang][1:],
                "answer_type": fact["type"],
                "category": fact["cat"],
                "source_citation": citation(fact),
            })
            meta.append({
                "id": item_id,
                "fact_id": fact["id"],
                "language": lang,
                "language_name": LANG_NAMES[lang],
                "glottocode": {"de": "stan1295", "fr": "stan1290", "it": "ital1282", "rm": "roma1326"}[lang],
                "article": fact["art"],
                "paragraph": fact["para"],
                "source_version": VERSION,
                "source_url": FEDLEX.format(date=VERSION, lang=lang) + f"#art_{fact['art']}",
                "evidence_span": fact["ev"][lang],
                "false_premise": fact["type"] == "false_premise",
                "license": "CDLA-Permissive-2.0",
                "license_note": LICENSE_NOTE,
                "contains_pii": False,
                "authoring": "Questions drafted with AI assistance (Claude), grounded by automated evidence-span check against the official text; see report.",
            })
    for name, data in (("eval.jsonl", rows), ("metadata.jsonl", meta)):
        with open(OUT / name, "w", encoding="utf-8") as fh:
            for r in data:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    digest = hashlib.sha256((OUT / "eval.jsonl").read_bytes()).hexdigest()
    print(f"wrote {len(rows)} items from {len(facts)} facts; eval.jsonl sha256={digest}")


if __name__ == "__main__":
    main()
