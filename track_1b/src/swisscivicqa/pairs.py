"""Pairwise cross-lingual answer comparison for ALL items (extends the deterministic signal in signal.py).

For every fact and every pair of languages, an LLM decides whether the two answers state the same core
fact. The comparison never sees the gold answer, so the resulting agreement score is reference-free.

Usage: python -m swisscivicqa.pairs --responses data/results/responses_X.jsonl \
           --judge-url http://127.0.0.1:8089/v1 --judge-model gemma-3-12b-it-q4_k_m
Output: data/results/pairs_X.jsonl (resumable)
"""
import argparse
import itertools
import json
import re
import urllib.request
from collections import defaultdict
from pathlib import Path

from .paths import project_root
from .signal import auroc

ROOT = project_root()
LANGS = ("de", "fr", "it", "rm")
NAMES = {"de": "German", "fr": "French", "it": "Italian", "rm": "Romansh"}
PROMPT = """Two answers to the same question about the Swiss Federal Constitution were given in different languages.
Decide whether they state the SAME core factual answer (same number, same institution, same yes/no, same list).
Ignore language, wording, formatting and extra detail that does not contradict. Do not judge correctness.

Question (German version, for reference): {question}
Answer A ({la}): {a}
Answer B ({lb}): {b}

Reply with exactly one word: SAME or DIFFERENT."""


def ask(url: str, model: str, prompt: str) -> str:
    body = {"model": model, "messages": [{"role": "user", "content": prompt}], "temperature": 0, "seed": 42, "max_tokens": 4}
    req = urllib.request.Request(f"{url}/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def run(args) -> None:
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    responses = {r["id"]: r["response"] for r in map(json.loads, open(args.responses, encoding="utf-8"))}
    out = Path(str(args.responses).replace("responses_", "pairs_"))
    done = set()
    if out.exists():
        done = {(d["fact_id"], d["a"], d["b"]) for d in map(json.loads, open(out, encoding="utf-8"))}
    facts = sorted({it["fact_id"] for it in items.values()})
    with open(out, "a", encoding="utf-8") as fh:
        for n, fid in enumerate(facts, 1):
            for la, lb in itertools.combinations(LANGS, 2):
                if (fid, la, lb) in done:
                    continue
                raw = ask(args.judge_url, args.judge_model, PROMPT.format(
                    question=items[f"{fid}-de"]["question"], la=NAMES[la], lb=NAMES[lb],
                    a=responses[f"{fid}-{la}"].strip(), b=responses[f"{fid}-{lb}"].strip()))
                m = re.search(r"SAME|DIFFERENT", raw.upper())
                fh.write(json.dumps({"fact_id": fid, "a": la, "b": lb, "same": (m.group(0) == "SAME") if m else None,
                                     "raw": raw, "judge_model": args.judge_model}) + "\n")
                fh.flush()
            print(f"[{n}/{len(facts)}] {fid}", flush=True)


def evaluate(items: dict, pairs: list, labels: dict) -> dict:
    """Agreement per item = share of the other three languages judged SAME; AUROC against the judge labels."""
    same = defaultdict(dict)
    for p in pairs:
        if p["same"] is not None:
            same[(p["fact_id"], p["a"])][p["b"]] = p["same"]
            same[(p["fact_id"], p["b"])][p["a"]] = p["same"]
    rows = []
    for item_id, it in items.items():
        others = same.get((it["fact_id"], it["language"]), {})
        if len(others) == len(LANGS) - 1 and item_id in labels:
            rows.append((sum(others.values()) / len(others), labels[item_id] == "CORRECT", it["answer_type"]))
    res = {"n": len(rows)}
    for name, test in (("agree_all", lambda s: s == 1.0), ("agree_some", lambda s: 0 < s < 1), ("agree_none", lambda s: s == 0)):
        sel = [c for s, c, _ in rows if test(s)]
        res[name] = {"n": len(sel), "p_correct": round(sum(sel) / len(sel), 4) if sel else None}
    a = auroc([s for s, c, _ in rows if c], [s for s, c, _ in rows if not c])
    res["auroc"] = round(a, 4) if a is not None else None
    by_type = {}
    for t in sorted({r[2] for r in rows}):
        sub = [r for r in rows if r[2] == t]
        a = auroc([s for s, c, _ in sub if c], [s for s, c, _ in sub if not c])
        by_type[t] = round(a, 4) if a is not None else None
    res["auroc_by_type"] = by_type
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--judge-url", required=True)
    ap.add_argument("--judge-model", required=True)
    run(ap.parse_args())


if __name__ == "__main__":
    main()
