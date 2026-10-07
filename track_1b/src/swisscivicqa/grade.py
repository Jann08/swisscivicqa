"""Grade model responses: SimpleQA-style three-way labels from an LLM judge, plus an
independent rule-based check for number and yes/no items (used to audit the judge).

Labels: CORRECT, INCORRECT, NOT_ATTEMPTED.

Usage: python -m swisscivicqa.grade --responses data/results/responses_X.jsonl \
           --judge-url http://127.0.0.1:8089/v1 --judge-model gemma-3-12b-it-q4_k_m
"""
import argparse
import json
import re
import time
import urllib.request
from pathlib import Path

from .paths import project_root

ROOT = project_root()
LABELS = {"A": "CORRECT", "B": "INCORRECT", "C": "NOT_ATTEMPTED"}

# Adapted from the SimpleQA grader template (openai/simple-evals, MIT licence).
JUDGE_TEMPLATE = """Your job is to grade a predicted answer to a question about the Swiss Federal Constitution against a gold target. The question and answers are in {language}. Assign one of: ["CORRECT", "INCORRECT", "NOT_ATTEMPTED"].

Rules:
- CORRECT: the predicted answer fully contains the important information of the gold target and contains no statement that contradicts it. Wording, language variants, number formatting (100 000 / 100'000 / 100000), capitalisation and extra correct detail do not matter. Hedging is fine as long as the gold target is stated and not contradicted.
- INCORRECT: any factual statement in the predicted answer contradicts the gold target, or the answer gives a different value, institution or yes/no. An answer that lists several candidates including a wrong one is INCORRECT.
- NOT_ATTEMPTED: the important information of the gold target is missing but nothing contradicts it (e.g. "I don't know", a refusal, or an answer that is off-topic without making a wrong claim).
- For list questions, the answer must name all elements of the gold target to be CORRECT; missing elements without wrong ones is NOT_ATTEMPTED, any wrong element is INCORRECT.
{extra}
Question: {question}
Gold target: {gold}{aliases}
Predicted answer: {response}

Grade the predicted answer as one of:
A: CORRECT
B: INCORRECT
C: NOT_ATTEMPTED

Just return the letter "A", "B", or "C", with no text around it."""

FALSE_PREMISE_EXTRA = """- This question contains a FALSE PREMISE. The gold target states the correction.
  CORRECT: the answer rejects or corrects the false premise (consistent with the gold target).
  INCORRECT: the answer accepts the false premise (answers as if it were true) or makes another contradicting claim.
  NOT_ATTEMPTED: the answer neither accepts nor corrects the premise (e.g. says it does not know)."""

LANG_NAMES = {"de": "German", "fr": "French", "it": "Italian", "rm": "Romansh"}
YES = {"de": ("ja",), "fr": ("oui",), "it": ("sì", "si"), "rm": ("gea", "schon")}
NO = {"de": ("nein",), "fr": ("non",), "it": ("no",), "rm": ("na", "betg")}


NUMBER_WORDS = {
    "de": "null eins zwei drei vier fünf sechs sieben acht neun zehn elf zwölf".split(),
    "fr": "zéro un deux trois quatre cinq six sept huit neuf dix onze douze".split(),
    "it": "zero uno due tre quattro cinque sei sette otto nove dieci undici dodici".split(),
    "rm": "nulla in dus trais quatter tschintg sis set otg nov diesch indesch dudesch".split(),
}


def numbers(text: str, lang: str = "") -> set:
    if lang in NUMBER_WORDS:
        # Whole-word number words from 2 upwards; 0/1 ("un", "in", ...) double as articles.
        words = NUMBER_WORDS[lang]
        text = re.sub(r"\b(" + "|".join(words[2:]) + r")\b",
                      lambda m: str(words.index(m.group(1).lower())), text, flags=re.I)
    text = text.replace(" ", " ").replace(" ", " ")
    text = re.sub(r"(?<=\d)['’ .](?=\d{3}\b)", "", text)  # 100'000 / 100 000 / 100.000 -> 100000
    return {n.replace(",", ".") for n in re.findall(r"\d+(?:[.,]\d+)?", text)}


def rule_grade(item: dict, response: str):
    """Return a label for number/yes_no items when the rule is unambiguous, else None."""
    lang, kind = item["language"], item["answer_type"]
    if kind == "number":
        gold = numbers(" ".join([item["gold_answer"], *item["gold_aliases"]]), lang)
        pred = numbers(response, lang)
        if not gold or not pred:
            return None
        if pred & gold:
            return "CORRECT" if len(pred - gold) == 0 else None  # extra numbers: leave to judge
        return "INCORRECT"
    if kind == "yes_no":
        first = re.split(r"[\s,.;:!]+", response.strip().lower(), maxsplit=1)[0]
        gold_yes = item["gold_answer"].strip().lower().startswith(YES[lang])
        if first in YES[lang]:
            return "CORRECT" if gold_yes else "INCORRECT"
        if first in NO[lang]:
            return "INCORRECT" if gold_yes else "CORRECT"
    return None


def judge(url: str, model: str, item: dict, response: str) -> tuple:
    aliases = f" (also acceptable: {'; '.join(item['gold_aliases'])})" if item["gold_aliases"] else ""
    prompt = JUDGE_TEMPLATE.format(
        language=LANG_NAMES[item["language"]], question=item["question"], gold=item["gold_answer"],
        aliases=aliases, response=response.strip(),
        extra=FALSE_PREMISE_EXTRA if item["answer_type"] == "false_premise" else "")
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}],
                       "temperature": 0.0, "max_tokens": 4, "seed": 42}).encode()
    req = urllib.request.Request(f"{url}/chat/completions", data=body, headers={"Content-Type": "application/json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                raw = json.load(r)["choices"][0]["message"]["content"]
            break
        except OSError:
            if attempt == 2:
                raise
            time.sleep(5)
    m = re.search(r"\b([ABC])\b", raw.strip())
    return (LABELS[m.group(1)] if m else None), raw


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--responses", required=True)
    ap.add_argument("--judge-url", required=True)
    ap.add_argument("--judge-model", required=True)
    ap.add_argument("--dataset", default=str(ROOT / "data" / "dataset" / "eval.jsonl"))
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    items = {i["id"]: i for i in map(json.loads, open(args.dataset, encoding="utf-8"))}
    responses = [json.loads(l) for l in open(args.responses, encoding="utf-8") if l.strip()]
    out = Path(args.out or str(args.responses).replace("responses_", "judgments_"))
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in open(out, encoding="utf-8") if l.strip()}
    with open(out, "a", encoding="utf-8") as fh:
        for n, r in enumerate(responses, 1):
            if r["id"] in done:
                continue
            item = items[r["id"]]
            label, raw = judge(args.judge_url, args.judge_model, item, r["response"])
            fh.write(json.dumps({
                "id": r["id"], "judge_model": args.judge_model, "judge_label": label, "judge_raw": raw,
                "rule_label": rule_grade(item, r["response"]),
            }, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"[{n}/{len(responses)}] {r['id']} {label}", flush=True)


if __name__ == "__main__":
    main()
