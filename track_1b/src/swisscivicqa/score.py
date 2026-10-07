"""Compute metrics from judgments (and, if present, human review labels).

Metrics (SimpleQA conventions):
  accuracy            = correct / all items
  correct_given_att.  = correct / (correct + incorrect)
  hallucination_rate  = incorrect / (correct + incorrect)
  f_score             = harmonic mean of accuracy and correct_given_attempted
Cross-lingual:
  consistency@4       = share of facts answered correctly in all four languages
  any@4               = share of facts answered correctly in at least one language
Confidence intervals: 95% percentile bootstrap over facts (seeded, 2000 resamples).

Usage: python -m swisscivicqa.score --judgments data/results/judgments_X.jsonl [--out results.json]
"""
import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("de", "fr", "it", "rm")


def rates(labels: list) -> dict:
    n = len(labels)
    c = labels.count("CORRECT")
    i = labels.count("INCORRECT")
    na = labels.count("NOT_ATTEMPTED")
    acc = c / n if n else 0.0
    cga = c / (c + i) if c + i else 0.0
    return {
        "n": n, "correct": c, "incorrect": i, "not_attempted": na,
        "accuracy": round(acc, 4),
        "correct_given_attempted": round(cga, 4),
        "hallucination_rate": round(i / (c + i), 4) if c + i else 0.0,
        "f_score": round(2 * acc * cga / (acc + cga), 4) if acc + cga else 0.0,
    }


def bootstrap_ci(facts: list, by_fact: dict, lang: str, seed: int = 42, reps: int = 2000) -> list:
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        sample = [rng.choice(facts) for _ in facts]
        labels = [by_fact[f][lang] for f in sample if lang in by_fact[f]]
        vals.append(labels.count("CORRECT") / len(labels) if labels else 0.0)
    vals.sort()
    return [round(vals[int(0.025 * reps)], 4), round(vals[int(0.975 * reps) - 1], 4)]


def cohen_kappa(a: list, b: list) -> float:
    cats = sorted(set(a) | set(b))
    n = len(a)
    if n == 0:
        return float("nan")
    po = sum(x == y for x, y in zip(a, b)) / n
    pe = sum((a.count(c) / n) * (b.count(c) / n) for c in cats)
    return round((po - pe) / (1 - pe), 4) if pe < 1 else 1.0


def compute(items: dict, judgments: list, human: list) -> dict:
    final = {j["id"]: j["judge_label"] for j in judgments}
    by_fact = defaultdict(dict)
    for item_id, label in final.items():
        it = items[item_id]
        by_fact[it["fact_id"]][it["language"]] = label
    facts = sorted(by_fact)

    res = {"overall": rates(list(final.values())), "by_language": {}, "by_type": {}, "by_category": {}}
    for lang in LANGS:
        labels = [l for i, l in final.items() if items[i]["language"] == lang]
        res["by_language"][lang] = {**rates(labels), "accuracy_ci95": bootstrap_ci(facts, by_fact, lang)}
    for key, field in (("by_type", "answer_type"), ("by_category", "category")):
        groups = defaultdict(lambda: defaultdict(list))
        for i, l in final.items():
            groups[items[i][field]][items[i]["language"]].append(l)
        res[key] = {g: {lang: rates(v[lang])["accuracy"] for lang in LANGS} for g, v in sorted(groups.items())}

    complete = [f for f in facts if len(by_fact[f]) == len(LANGS)]
    all4 = [f for f in complete if all(by_fact[f][l] == "CORRECT" for l in LANGS)]
    any4 = [f for f in complete if any(by_fact[f][l] == "CORRECT" for l in LANGS)]
    res["cross_lingual"] = {
        "facts": len(complete),
        "consistency_at_4": round(len(all4) / len(complete), 4) if complete else 0.0,
        "any_at_4": round(len(any4) / len(complete), 4) if complete else 0.0,
        "known_somewhere_but_not_everywhere": len(any4) - len(all4),
        "pairwise_agreement": {
            f"{a}-{b}": round(sum(by_fact[f][a] == by_fact[f][b] for f in complete) / len(complete), 4)
            for idx, a in enumerate(LANGS) for b in LANGS[idx + 1:]
        } if complete else {},
    }

    ruled = [j for j in judgments if j.get("rule_label")]
    res["judge_vs_rules"] = {
        "n": len(ruled),
        "agreement": round(sum(j["rule_label"] == j["judge_label"] for j in ruled) / len(ruled), 4) if ruled else None,
        "cohen_kappa": cohen_kappa([j["rule_label"] for j in ruled], [j["judge_label"] for j in ruled]) if ruled else None,
    }
    if human:
        by_item = defaultdict(dict)
        for h in human:
            by_item[h["id"]][h["annotator"]] = h["human_label"]
        consensus = {}
        for item_id, labels in by_item.items():
            counts = defaultdict(int)
            for a in sorted(labels):
                counts[labels[a]] += 1
            best = max(counts.values())
            # Majority label; ties go to the alphabetically first annotator's label.
            consensus[item_id] = next(labels[a] for a in sorted(labels) if counts[labels[a]] == best)
        ids = sorted(i for i in consensus if i in final)
        h_lab, j_lab = [consensus[i] for i in ids], [final[i] for i in ids]
        res["judge_vs_human"] = {
            "n": len(ids),
            "annotators": sorted({h["annotator"] for h in human}),
            "agreement": round(sum(a == b for a, b in zip(h_lab, j_lab)) / len(ids), 4) if ids else None,
            "cohen_kappa": cohen_kappa(h_lab, j_lab) if ids else None,
            "human_accuracy_on_sample": round(h_lab.count("CORRECT") / len(ids), 4) if ids else None,
            "judge_accuracy_on_sample": round(j_lab.count("CORRECT") / len(ids), 4) if ids else None,
            "by_language": {
                lang: round(sum(consensus[i] == final[i] for i in ids if items[i]["language"] == lang)
                            / max(1, sum(items[i]["language"] == lang for i in ids)), 4)
                for lang in LANGS
            },
        }
        multi = [i for i in ids if len(by_item[i]) >= 2]
        if multi:
            first = [by_item[i][sorted(by_item[i])[0]] for i in multi]
            second = [by_item[i][sorted(by_item[i])[1]] for i in multi]
            res["inter_annotator"] = {
                "n": len(multi),
                "agreement": round(sum(a == b for a, b in zip(first, second)) / len(multi), 4),
                "cohen_kappa": cohen_kappa(first, second),
            }
    return res


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--judgments", required=True)
    ap.add_argument("--human", default=str(ROOT / "data" / "human_review" / "review.jsonl"))
    ap.add_argument("--dataset", default=str(ROOT / "data" / "dataset" / "eval.jsonl"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()
    items = {i["id"]: i for i in map(json.loads, open(args.dataset, encoding="utf-8"))}
    judgments = [json.loads(l) for l in open(args.judgments, encoding="utf-8") if l.strip()]
    human = []
    if Path(args.human).exists():
        human = [json.loads(l) for l in open(args.human, encoding="utf-8") if l.strip()]
    res = compute(items, judgments, human)
    text = json.dumps(res, indent=1, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
