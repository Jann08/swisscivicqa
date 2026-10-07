"""Spreadsheet workflow for the blind human review (alternative to the terminal tool).

export: write the 20% audit sample as a CSV (UTF-8 with BOM, ';' separated, opens in Excel/LibreOffice)
        plus an instruction sheet. Judge labels are NOT included (blind review).
import: read filled-in CSVs (column "bewertung" = 1/2/3) into data/human_review/review.jsonl.

Usage:
  python -m swisscivicqa.review_sheet export --responses data/results/responses_X.jsonl --out DIR [--split 2]
  python -m swisscivicqa.review_sheet import --annotator A2 FILE.csv [FILE.csv ...]
"""
import argparse
import csv
import json
import time
from pathlib import Path

from .review import GUIDE, KEYS, OUT_DIR, ROOT, sample_ids

COLUMNS = ["id", "sprache", "typ", "frage", "musterantwort", "auch_ok", "frage_deutsch", "antwort_deutsch",
           "apertus_antwort", "bewertung"]
INSTRUCTIONS = """BEWERTUNG SwissCivicQA (Hack Apertus) - Anleitung
==================================================

Danke fuers Mitmachen! Du vergleichst Antworten einer KI (Apertus) mit der richtigen Antwort
aus der Bundesverfassung. Du brauchst kein Vorwissen: die richtige Antwort steht immer daneben.

So geht's:
- Datei in Excel oder LibreOffice oeffnen.
- Pro Zeile: Spalte "apertus_antwort" mit "musterantwort" vergleichen
  (bei Franzoesisch/Italienisch/Raetoromanisch helfen "frage_deutsch" und "antwort_deutsch").
- In die letzte Spalte "bewertung" GENAU EINE Zahl schreiben: 1, 2 oder 3.
- Nichts anderes veraendern, keine Zeilen loeschen oder sortieren. Speichern als CSV.
- Bitte KEINE KI (ChatGPT o.ae.) zum Bewerten benutzen: es geht genau darum, dass ein
  Mensch die KI-Bewertung kontrolliert.
- Teilnahme ab 18 Jahren. Deine Bewertungen werden nur unter einem Kuerzel (z. B. A2)
  veroeffentlicht, nie mit Namen.
{guide}
Beispiele:
- Musterantwort "7", Apertus "Sieben Mitglieder."            -> 1
- Musterantwort "100 000", Apertus "80 000"                 -> 2
- Musterantwort "die Bundesversammlung", Apertus "Das Volk" -> 2
- Apertus "Das kann ich nicht sicher sagen."                -> 3
- Fangfrage "Warum hat der Bundesrat neun Mitglieder?",
  Apertus "Weil ... neun Mitglieder ..."                    -> 2 (falsche Annahme uebernommen)
  Apertus "Er hat nicht neun, sondern sieben Mitglieder."   -> 1
"""


def export(args) -> None:
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    responses = {r["id"]: r for r in map(json.loads, open(args.responses, encoding="utf-8"))}
    ids = [i for i in sample_ids(items) if i in responses]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    parts = [ids[k::args.split] for k in range(args.split)]
    for n, part in enumerate(parts, 1):
        name = out / (f"bewertung_teil{n}.csv" if args.split > 1 else "bewertung.csv")
        with open(name, "w", encoding="utf-8-sig", newline="") as fh:
            w = csv.writer(fh, delimiter=";")
            w.writerow(COLUMNS)
            for item_id in part:
                it = items[item_id]
                de = items[f"{it['fact_id']}-de"]
                w.writerow([item_id, it["language"].upper(),
                            "FANGFRAGE (falsche Annahme)" if it["answer_type"] == "false_premise" else it["answer_type"],
                            it["question"], it["gold_answer"], "; ".join(it["gold_aliases"]),
                            "" if it["language"] == "de" else de["question"],
                            "" if it["language"] == "de" else de["gold_answer"],
                            responses[item_id]["response"].strip(), ""])
        print(f"wrote {name} ({len(part)} rows)")
    (out / "ANLEITUNG.txt").write_text(INSTRUCTIONS.format(guide=GUIDE), encoding="utf-8")
    print(f"wrote {out / 'ANLEITUNG.txt'}")


TXT_MARK = ">>> BEWERTUNG (1/2/3):"


def export_txt(args) -> None:
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    responses = {r["id"]: r for r in map(json.loads, open(args.responses, encoding="utf-8"))}
    ids = [i for i in sample_ids(items) if i in responses]
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    lines = [INSTRUCTIONS.format(guide=GUIDE).replace(
        "- Datei in Excel oder LibreOffice oeffnen.\n", "- Datei in einem Texteditor oeffnen (Editor/Notepad, TextEdit, ...).\n").replace(
        "- In die letzte Spalte \"bewertung\" GENAU EINE Zahl schreiben: 1, 2 oder 3.\n",
        f"- Hinter jedes \"{TXT_MARK}\" GENAU EINE Zahl schreiben: 1, 2 oder 3.\n").replace(
        "keine Zeilen loeschen oder sortieren. Speichern als CSV.", "keine Zeilen loeschen. Normal speichern.").replace(
        "- Pro Zeile: Spalte \"apertus_antwort\" mit \"musterantwort\" vergleichen\n  (bei Franzoesisch/Italienisch/Raetoromanisch helfen \"frage_deutsch\" und \"antwort_deutsch\").",
        "- Pro Block: APERTUS mit RICHTIGE ANTWORT vergleichen\n  (bei Franzoesisch/Italienisch/Raetoromanisch helfen die deutschen Zeilen)."),
        "", "Dein Kuerzel (z. B. Vorname-Initiale, wird NICHT veroeffentlicht): ", "", ""]
    for n, item_id in enumerate(ids, 1):
        it = items[item_id]
        de = items[f"{it['fact_id']}-de"]
        lines += ["=" * 70,
                  f"{n}/{len(ids)}  [{item_id}]  Sprache: {it['language'].upper()}"
                  + ("   ** FANGFRAGE: enthaelt eine falsche Annahme **" if it["answer_type"] == "false_premise" else ""),
                  f"FRAGE:            {it['question']}",
                  f"RICHTIGE ANTWORT: {it['gold_answer']}" + (f"   (auch ok: {'; '.join(it['gold_aliases'])})" if it["gold_aliases"] else "")]
        if it["language"] != "de":
            lines += [f"  Frage deutsch:   {de['question']}", f"  Antwort deutsch: {de['gold_answer']}"]
        lines += [f"APERTUS:          {responses[item_id]['response'].strip()}", f"{TXT_MARK} ", ""]
    name = out / "bewertung.txt"
    name.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {name} ({len(ids)} items)")


def read_txt(path: str) -> list:
    rows, current = [], None
    for line in open(path, encoding="utf-8-sig"):
        if line.startswith("=" * 10):
            current = None
        elif "  [" in line and "]  Sprache:" in line:
            current = line.split("[", 1)[1].split("]", 1)[0]
        elif line.startswith(TXT_MARK) and current:
            rows.append({"id": current, "bewertung": line[len(TXT_MARK):].strip()})
            current = None
    return rows


def import_(args) -> None:
    rows, problems = [], []
    for path in [p for p in args.files if p.endswith(".txt")]:
        for r in read_txt(path):
            val = r["bewertung"].strip().rstrip(".")
            if val not in KEYS:
                problems.append(f"{path}: {r['id']} {'leer' if not val else 'ungueltiger Wert ' + repr(val)}")
                continue
            rows.append({"id": r["id"], "human_label": KEYS[val], "annotator": args.annotator,
                         "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "text_file"})
    args.files = [p for p in args.files if not p.endswith(".txt")]
    for path in args.files:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            sample = fh.read(4096)
            fh.seek(0)
            delim = ";" if sample.count(";") >= sample.count(",") else ","
            for r in csv.DictReader(fh, delimiter=delim):
                val = (r.get("bewertung") or "").strip()
                if not val:
                    problems.append(f"{path}: {r.get('id')} leer")
                    continue
                if val not in KEYS:
                    problems.append(f"{path}: {r.get('id')} ungueltiger Wert {val!r}")
                    continue
                rows.append({"id": r["id"], "human_label": KEYS[val], "annotator": args.annotator,
                             "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"), "source": "spreadsheet"})
    for p in problems:
        print("WARN", p)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / "review.jsonl"
    existing = [json.loads(l) for l in open(out, encoding="utf-8")] if out.exists() else []
    keep = [e for e in existing if e["annotator"] != args.annotator]  # re-import replaces this annotator
    with open(out, "w", encoding="utf-8") as fh:
        for e in keep + rows:
            fh.write(json.dumps(e, ensure_ascii=False) + "\n")
    print(f"imported {len(rows)} labels for {args.annotator} ({len(problems)} problems); {out} now has {len(keep) + len(rows)} labels")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("export-txt")
    t.add_argument("--responses", required=True)
    t.add_argument("--out", required=True)
    e = sub.add_parser("export")
    e.add_argument("--responses", required=True)
    e.add_argument("--out", required=True)
    e.add_argument("--split", type=int, default=1)
    i = sub.add_parser("import")
    i.add_argument("--annotator", required=True)
    i.add_argument("files", nargs="+")
    args = ap.parse_args()
    {"export": export, "export-txt": export_txt, "import": import_}[args.cmd](args)


if __name__ == "__main__":
    main()
