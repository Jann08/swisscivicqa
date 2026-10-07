"""Print constitution articles side by side, as used by annotators when writing items.

Usage: python -m swisscivicqa.show [--langs de,fr,it,rm] ART [ART ...]
"""
import argparse
import json
from pathlib import Path

from .paths import project_root

PROCESSED = project_root() / "data" / "processed"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("articles", nargs="+")
    ap.add_argument("--langs", default="de")
    ap.add_argument("--width", type=int, default=400)
    args = ap.parse_args()
    texts = {l: json.loads((PROCESSED / f"bv_{l}.json").read_text(encoding="utf-8")) for l in args.langs.split(",")}
    for art in args.articles:
        for lang, articles in texts.items():
            a = articles[art]
            print(f"## Art. {art} [{lang}] {a['title']}")
            for p in a["paragraphs"]:
                print(f"   {p['para']} {p['text'][:args.width]}")


if __name__ == "__main__":
    main()
