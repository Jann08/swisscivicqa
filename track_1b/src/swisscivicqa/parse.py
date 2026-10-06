"""Parse the official Fedlex HTML of the Swiss Federal Constitution (SR 101) into
article/paragraph JSON, one file per language.

Usage: python -m swisscivicqa.parse data/raw data/processed
"""
import html
import json
import re
import sys
from pathlib import Path

LANGS = ("de", "fr", "it", "rm")
VERSION = "20240303"

ARTICLE_RE = re.compile(r'<article id="art_([^"]+)">(.*?)</article>', re.S)
HEADING_RE = re.compile(r"<h6[^>]*>(.*?)</h6>", re.S)
PARA_RE = re.compile(r'<p class="absatz[^"]*">(.*?)</p>', re.S)
FOOTNOTE_REF_RE = re.compile(r'<sup><a href="#fn-[^"]*"[^>]*>.*?</a></sup>', re.S)
LEADING_NUM_RE = re.compile(r"^\s*(?:<inl>)?<sup>([^<]*)</sup>(?:</inl>)?", re.S)


def clean(fragment: str) -> str:
    text = FOOTNOTE_REF_RE.sub("", fragment)
    text = html.unescape(re.sub(r"<[^>]+>", " ", text))
    return re.sub(r"\s+", " ", text).strip()


def blocks(body: str):
    """Yield ("p", inner_html) and ("dl", outer_html) in document order; dl may be nested."""
    pos = 0
    while True:
        p = PARA_RE.search(body, pos)
        d = body.find("<dl", pos)
        if p is None and d == -1:
            return
        if d != -1 and (p is None or d < p.start()):
            depth, i = 0, d
            while True:
                nxt_open = body.find("<dl", i + 1)
                nxt_close = body.find("</dl>", i + 1)
                if nxt_close == -1:
                    raise ValueError("unbalanced <dl>")
                if nxt_open != -1 and nxt_open < nxt_close:
                    depth, i = depth + 1, nxt_open
                elif depth:
                    depth, i = depth - 1, nxt_close
                else:
                    end = nxt_close + len("</dl>")
                    break
            yield "dl", body[d:end]
            pos = end
        else:
            yield "p", p.group(1)
            pos = p.end()


def parse_file(path: Path) -> dict:
    source = path.read_text(encoding="utf-8")
    articles = {}
    for art_id, body in ARTICLE_RE.findall(source):
        body = re.sub(r'<div class="footnotes">.*?</div>', "", body, flags=re.S)
        heading = HEADING_RE.search(body)
        title = clean(heading.group(1)) if heading else ""
        title = re.sub(r"^Art\.\s*\S+\s*", "", title)
        paragraphs = []
        for kind, raw in blocks(body):
            if kind == "dl":
                # Lettered lists (a., b., ...) belong to the preceding paragraph.
                items = clean(raw)
                if paragraphs and items:
                    paragraphs[-1]["text"] += " " + items
                continue
            num = LEADING_NUM_RE.match(raw)
            label = html.unescape(num.group(1)).strip() if num else ""
            text = clean(LEADING_NUM_RE.sub("", raw, count=1))
            if text:
                paragraphs.append({"para": label, "text": text})
        articles[art_id] = {"article": art_id, "title": title, "paragraphs": paragraphs}
    if not articles:
        raise ValueError(f"no articles found in {path}")
    return articles


def main(raw_dir: str, out_dir: str) -> None:
    raw, out = Path(raw_dir), Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    counts = {}
    for lang in LANGS:
        articles = parse_file(raw / f"bv_{VERSION}_{lang}.html")
        (out / f"bv_{lang}.json").write_text(json.dumps(articles, ensure_ascii=False, indent=1), encoding="utf-8")
        counts[lang] = len(articles)
    if len(set(counts.values())) != 1:
        raise ValueError(f"article counts differ between languages: {counts}")
    print(f"parsed {counts}")


if __name__ == "__main__":
    main(*sys.argv[1:3])
