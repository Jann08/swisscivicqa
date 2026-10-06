"""Blind human review of a stratified 20% sample of graded responses (terminal tool).

The reviewer sees question, gold answer and model answer, but NOT the judge label,
so judge-human agreement is not inflated by anchoring. Resumable; Ctrl+C is safe.

Usage: python -m swisscivicqa.review --responses data/results/responses_X.jsonl
"""
import argparse
import json
import random
import time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "data" / "human_review"
KEYS = {"1": "CORRECT", "2": "INCORRECT", "3": "NOT_ATTEMPTED"}
GUIDE = """
Bewertungsregeln (gleiche Regeln wie der KI-Bewerter):
  1 = RICHTIG          Die Antwort enthaelt die Kerninformation der Musterantwort und widerspricht ihr nirgends.
                       Format egal (100'000 = 100 000), zusaetzliche korrekte Details sind ok.
  2 = FALSCH           Irgendeine Aussage widerspricht der Musterantwort (falsche Zahl, falsche Behoerde, falsches Ja/Nein,
                       oder bei Fangfragen: die falsche Annahme wird uebernommen).
  3 = NICHT BEANTWORTET Kerninformation fehlt, aber nichts Falsches (z. B. "weiss ich nicht").
  s = ueberspringen, q = speichern und beenden
Bei Fangfragen (FALSCHE ANNAHME) ist RICHTIG nur, wenn die Antwort die Annahme zurueckweist.
"""


def sample_ids(items: dict, fraction: float = 0.2, seed: int = 20261016) -> list:
    rng = random.Random(seed)
    by_lang = defaultdict(list)
    for i in sorted(items):
        by_lang[items[i]["language"]].append(i)
    picked = []
    for lang in sorted(by_lang):
        ids = by_lang[lang]
        picked += rng.sample(ids, round(len(ids) * fraction))
    rng.shuffle(picked)
    return picked


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--dataset", default=str(ROOT / "data" / "dataset" / "eval.jsonl"))
    ap.add_argument("--annotator", default="A1")
    args = ap.parse_args()

    items = {i["id"]: i for i in map(json.loads, open(args.dataset, encoding="utf-8"))}
    responses = {r["id"]: r for r in map(json.loads, open(args.responses, encoding="utf-8"))}
    ids = [i for i in sample_ids(items) if i in responses]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "sample_ids.json").write_text(json.dumps(ids, indent=0) + "\n", encoding="utf-8")
    out = OUT_DIR / "review.jsonl"
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")} if out.exists() else set()

    print(GUIDE)
    todo = [i for i in ids if i not in done]
    print(f"{len(done)} erledigt, {len(todo)} offen (Stichprobe: {len(ids)} = 20 % von {len(items)})\n")
    with open(out, "a", encoding="utf-8") as fh:
        for n, item_id in enumerate(todo, 1):
            it = items[item_id]
            print("=" * 78)
            print(f"[{n}/{len(todo)}] {item_id}  Sprache: {it['language'].upper()}  Typ: {it['answer_type']}"
                  + ("  ** FALSCHE ANNAHME **" if it["answer_type"] == "false_premise" else ""))
            print(f"FRAGE:          {it['question']}")
            print(f"MUSTERANTWORT:  {it['gold_answer']}" + (f"   (auch ok: {'; '.join(it['gold_aliases'])})" if it["gold_aliases"] else ""))
            if it["language"] != "de":
                de = items[f"{it['fact_id']}-de"]
                print(f"  (DE Frage:     {de['question']})")
                print(f"  (DE Antwort:   {de['gold_answer']})")
            print(f"QUELLE:         {it['source_citation']}")
            print(f"APERTUS:        {responses[item_id]['response'].strip()}")
            while True:
                key = input("Bewertung [1/2/3, s, q]: ").strip().lower()
                if key in KEYS or key in ("s", "q"):
                    break
            if key == "q":
                print("Gespeichert. Mit demselben Befehl geht es spaeter weiter.")
                return
            if key == "s":
                continue
            fh.write(json.dumps({"id": item_id, "human_label": KEYS[key], "annotator": args.annotator,
                                 "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}, ensure_ascii=False) + "\n")
            fh.flush()
    print("Fertig, danke!")


if __name__ == "__main__":
    main()
