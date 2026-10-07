"""Quality checks for the fact source files.

Every fact must be grounded in the official constitution text: for each language the
evidence snippet must occur verbatim (after whitespace/quote normalisation) in the cited
article/paragraph of that language's official version.

Usage: python -m swisscivicqa.validate
"""
import json
import re
import sys
from pathlib import Path

from .paths import project_root

ROOT = project_root()
LANGS = ("de", "fr", "it", "rm")
TYPES = {"number", "entity", "list", "yes_no", "false_premise"}
EXCLUDED_ARTICLES = {"127"}  # amended with effect from 2029-01-01, answer would change


def norm(text: str) -> str:
    text = text.replace("’", "'").replace("‘", "'").replace(" ", " ").replace(" ", " ")
    return re.sub(r"\s+", " ", text).strip().lower()


def load_facts() -> list:
    facts = []
    for path in sorted((ROOT / "data" / "source").glob("facts_*.json")):
        facts.extend(json.loads(path.read_text(encoding="utf-8")))
    return facts


def check(facts: list) -> list:
    texts = {l: json.loads((ROOT / "data" / "processed" / f"bv_{l}.json").read_text(encoding="utf-8")) for l in LANGS}
    errors, seen = [], set()
    for f in facts:
        fid = f.get("id", "?")
        if fid in seen:
            errors.append(f"{fid}: duplicate id")
        seen.add(fid)
        if f.get("type") not in TYPES:
            errors.append(f"{fid}: unknown type {f.get('type')}")
        if f["art"] in EXCLUDED_ARTICLES:
            errors.append(f"{fid}: article {f['art']} is excluded")
        for key in ("q", "a", "ev"):
            missing = [l for l in LANGS if not f.get(key, {}).get(l)]
            if missing:
                errors.append(f"{fid}: {key} missing for {missing}")
        for lang in LANGS:
            article = texts[lang].get(f["art"])
            if article is None:
                errors.append(f"{fid}: article {f['art']} not found [{lang}]")
                continue
            paras = [p for p in article["paragraphs"] if f["para"] in ("", p["para"])]
            if not paras:
                errors.append(f"{fid}: para {f['para']} not found in art {f['art']} [{lang}]")
                continue
            ev = norm(f["ev"][lang])
            if len(ev) < 8:
                errors.append(f"{fid}: evidence too short to be meaningful [{lang}]: {f['ev'][lang]!r}")
            if not any(ev in norm(p["text"]) for p in paras):
                errors.append(f"{fid}: evidence not in official text [{lang}]: {f['ev'][lang]!r}")
    return errors


def main() -> None:
    facts = load_facts()
    errors = check(facts)
    for e in errors:
        print("ERROR", e)
    by_type = {}
    for f in facts:
        by_type[f["type"]] = by_type.get(f["type"], 0) + 1
    print(f"{len(facts)} facts, {len(facts) * len(LANGS)} items, types={by_type}, errors={len(errors)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
