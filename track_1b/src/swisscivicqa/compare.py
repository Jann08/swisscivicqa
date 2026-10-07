"""Paired comparison of two models on the same items.

Accuracy differences use a paired bootstrap over facts (all four language items of a fact are
resampled together, 2000 resamples, seed 42) and an exact two-sided McNemar test on discordant items.
"""
import json
import random
from math import comb

LANGS = ("de", "fr", "it", "rm")


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(comb(n, i) for i in range(k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def paired(items: dict, labels_a: dict, labels_b: dict, seed: int = 42, reps: int = 2000) -> dict:
    by_fact = {}
    for item_id, it in items.items():
        if item_id in labels_a and item_id in labels_b:
            by_fact.setdefault(it["fact_id"], []).append(item_id)
    facts = sorted(by_fact)
    rng = random.Random(seed)
    res = {}
    for scope in ("all", *LANGS):
        ids = [i for f in facts for i in by_fact[f] if scope == "all" or items[i]["language"] == scope]
        a = [labels_a[i] == "CORRECT" for i in ids]
        b = [labels_b[i] == "CORRECT" for i in ids]
        diff = (sum(a) - sum(b)) / len(ids)
        boot = []
        for _ in range(reps):
            sample = [rng.choice(facts) for _ in facts]
            sel = [i for f in sample for i in by_fact[f] if scope == "all" or items[i]["language"] == scope]
            boot.append(sum((labels_a[i] == "CORRECT") - (labels_b[i] == "CORRECT") for i in sel) / len(sel))
        boot.sort()
        only_a = sum(x and not y for x, y in zip(a, b))
        only_b = sum(y and not x for x, y in zip(a, b))
        res[scope] = {"n": len(ids), "diff": round(diff, 4),
                      "ci95": [round(boot[int(0.025 * reps)], 4), round(boot[int(0.975 * reps) - 1], 4)],
                      "only_a_correct": only_a, "only_b_correct": only_b,
                      "mcnemar_p": round(mcnemar_exact(only_a, only_b), 4)}
    return res


def consistency_diff(items: dict, labels_a: dict, labels_b: dict) -> dict:
    by_fact = {}
    for item_id, it in items.items():
        by_fact.setdefault(it["fact_id"], []).append(item_id)
    all_a = [all(labels_a.get(i) == "CORRECT" for i in ids) for ids in by_fact.values()]
    all_b = [all(labels_b.get(i) == "CORRECT" for i in ids) for ids in by_fact.values()]
    only_a = sum(x and not y for x, y in zip(all_a, all_b))
    only_b = sum(y and not x for x, y in zip(all_a, all_b))
    return {"facts": len(all_a), "a": sum(all_a), "b": sum(all_b), "only_a": only_a, "only_b": only_b,
            "mcnemar_p": round(mcnemar_exact(only_a, only_b), 4)}


def load_labels(path) -> dict:
    return {j["id"]: j["judge_label"] for j in map(json.loads, open(path, encoding="utf-8")) if j}
