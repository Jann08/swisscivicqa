"""Cross-lingual agreement as a reference-free hallucination signal.

For number and yes/no items the answers of the four language versions of a fact can be compared
deterministically. An answer that agrees with the answers in the other languages is much more
likely to be correct, which needs neither a gold answer nor a second model at inference time.
"""
from collections import defaultdict

from .grade import NO, YES, numbers

LANGS = ("de", "fr", "it", "rm")


def answer_key(item: dict, response: str):
    if item["answer_type"] == "number":
        found = numbers(response, item["language"])
        return frozenset(found) if found else None
    if item["answer_type"] == "yes_no" and response.strip():
        first = response.strip().lower().split()[0].strip(".,;:!")
        if first in YES[item["language"]]:
            return "Y"
        if first in NO[item["language"]]:
            return "N"
    return None


def agreement_scores(items: dict, responses: dict) -> dict:
    """item id -> share of the other languages whose answer agrees with this one."""
    by_fact = defaultdict(dict)
    for item_id, it in items.items():
        if item_id in responses:
            by_fact[it["fact_id"]][it["language"]] = item_id
    scores = {}
    for ids in by_fact.values():
        keys = {lang: answer_key(items[i], responses[i]) for lang, i in ids.items()}
        for lang, item_id in ids.items():
            own = keys[lang]
            others = [k for o, k in keys.items() if o != lang and k is not None]
            if own is None or not others:
                continue
            if isinstance(own, frozenset):
                scores[item_id] = sum(bool(own & o) for o in others if isinstance(o, frozenset)) / len(others)
            else:
                scores[item_id] = sum(own == o for o in others) / len(others)
    return scores


def auroc(pos: list, neg: list):
    if not pos or not neg:
        return None
    return sum((p > n) + 0.5 * (p == n) for p in pos for n in neg) / (len(pos) * len(neg))


def evaluate(items: dict, responses: dict, labels: dict) -> dict:
    scores = agreement_scores(items, responses)
    rows = [(s, labels[i] == "CORRECT") for i, s in scores.items() if i in labels]
    bands = {"agree_all": (lambda s: s == 1.0), "agree_some": (lambda s: 0 < s < 1.0), "agree_none": (lambda s: s == 0)}
    out = {"n": len(rows)}
    for name, test in bands.items():
        sel = [c for s, c in rows if test(s)]
        out[name] = {"n": len(sel), "p_correct": round(sum(sel) / len(sel), 4) if sel else None}
    a = auroc([s for s, c in rows if c], [s for s, c in rows if not c])
    out["auroc"] = round(a, 4) if a is not None else None
    return out
