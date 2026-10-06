"""Render report figures as SVG (standard library only).

Usage: python -m swisscivicqa.figures results/metrics_X.json data/results/judgments_X.jsonl report/figures
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ("de", "fr", "it", "rm")
LANG_LABEL = {"de": "German", "fr": "French", "it": "Italian", "rm": "Romansh"}
# Validated (light mode, CVD-safe): blue = correct, orange = incorrect; neutral grey = not attempted.
C_CORRECT, C_INCORRECT, C_NA = "#2a78d6", "#eb6834", "#b8b6af"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e2dc", "#ffffff"
FONT = "font-family='Liberation Sans, Arial, sans-serif'"


def text(x, y, s, size=11, fill=INK, anchor="start", weight="normal"):
    return f"<text x='{x:.1f}' y='{y:.1f}' {FONT} font-size='{size}' fill='{fill}' text-anchor='{anchor}' font-weight='{weight}'>{s}</text>"


def outcomes_by_language(metrics: dict) -> str:
    """Stacked 100% bars per language: correct | not attempted | incorrect, with CI text."""
    w, left, right, top, bar_h, gap = 620, 80, 150, 46, 30, 16
    plot_w = w - left - right
    h = top + len(LANGS) * (bar_h + gap) + 30
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>",
           f"<rect width='{w}' height='{h}' fill='{SURFACE}'/>"]
    legend = [("Correct", C_CORRECT), ("Not attempted", C_NA), ("Incorrect", C_INCORRECT)]
    lx = left
    for name, col in legend:
        out.append(f"<rect x='{lx}' y='14' width='12' height='12' rx='2' fill='{col}'/>")
        out.append(text(lx + 17, 24, name, 11, INK2))
        lx += 17 + len(name) * 6.4 + 22
    for frac in (0, 0.25, 0.5, 0.75, 1.0):
        x = left + frac * plot_w
        out.append(f"<line x1='{x:.1f}' x2='{x:.1f}' y1='{top - 6}' y2='{h - 26}' stroke='{GRID}' stroke-width='1'/>")
        out.append(text(x, h - 12, f"{int(frac * 100)}%", 10, INK2, "middle"))
    for i, lang in enumerate(LANGS):
        m = metrics["by_language"][lang]
        y = top + i * (bar_h + gap)
        out.append(text(left - 10, y + bar_h / 2 + 4, LANG_LABEL[lang], 12, INK, "end"))
        x = left
        segs = [(m["correct"], C_CORRECT, "#ffffff"), (m["not_attempted"], C_NA, INK), (m["incorrect"], C_INCORRECT, INK)]
        for k, (count, col, label_ink) in enumerate(segs):
            seg_w = plot_w * count / m["n"]
            if seg_w <= 0:
                continue
            draw_w = max(seg_w - (2 if k < 2 else 0), 0.5)  # 2px surface gap between segments
            out.append(f"<rect x='{x:.1f}' y='{y}' width='{draw_w:.1f}' height='{bar_h}' fill='{col}'/>")
            if seg_w > 34:
                out.append(text(x + seg_w / 2, y + bar_h / 2 + 4, f"{100 * count / m['n']:.0f}%", 11, label_ink, "middle", "bold"))
            x += seg_w
        lo, hi = m["accuracy_ci95"]
        out.append(text(left + plot_w + 10, y + bar_h / 2 - 2, f"acc. {100 * m['accuracy']:.1f}%", 11, INK))
        out.append(text(left + plot_w + 10, y + bar_h / 2 + 12, f"95% CI {100 * lo:.0f}–{100 * hi:.0f}%", 10, INK2))
    out.append("</svg>")
    return "\n".join(out)


def consistency_histogram(items: dict, judgments: list) -> str:
    """Number of facts by how many of the four languages were answered correctly."""
    per_fact = defaultdict(int)
    facts = set()
    for j in judgments:
        fid = items[j["id"]]["fact_id"]
        facts.add(fid)
        per_fact[fid] += j["judge_label"] == "CORRECT"
    counts = Counter(per_fact[f] for f in facts)
    w, h, left, top, bottom = 420, 230, 44, 20, 46
    plot_h, plot_w = h - top - bottom, w - left - 16
    ymax = max(counts.values()) if counts else 1
    step = 10 if ymax > 30 else 5
    ytop = ((ymax // step) + 1) * step
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>",
           f"<rect width='{w}' height='{h}' fill='{SURFACE}'/>"]
    for v in range(0, ytop + 1, step):
        y = top + plot_h - plot_h * v / ytop
        out.append(f"<line x1='{left}' x2='{w - 16}' y1='{y:.1f}' y2='{y:.1f}' stroke='{GRID}' stroke-width='1'/>")
        out.append(text(left - 6, y + 4, str(v), 10, INK2, "end"))
    bw = plot_w / 5
    for k in range(5):
        c = counts.get(k, 0)
        bh = plot_h * c / ytop
        x = left + k * bw + bw * 0.2
        y = top + plot_h - bh
        if bh > 0:
            r = min(4, bh)
            # rounded data end (top), square baseline
            out.append(f"<path d='M{x:.1f},{top + plot_h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
                       f"H{x + bw * 0.6 - r:.1f} Q{x + bw * 0.6:.1f},{y:.1f} {x + bw * 0.6:.1f},{y + r:.1f} "
                       f"V{top + plot_h:.1f} Z' fill='{C_CORRECT}'/>")
        out.append(text(x + bw * 0.3, y - 5, str(c), 11, INK, "middle", "bold"))
        out.append(text(x + bw * 0.3, top + plot_h + 16, f"{k}/4", 11, INK2, "middle"))
    out.append(text(left + plot_w / 2, h - 8, "languages in which the fact was answered correctly", 11, INK2, "middle"))
    out.append("</svg>")
    return "\n".join(out)


def main() -> None:
    metrics_path, judgments_path, out_dir = sys.argv[1:4]
    metrics = json.loads(Path(metrics_path).read_text(encoding="utf-8"))
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    judgments = [json.loads(l) for l in open(judgments_path, encoding="utf-8") if l.strip()]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "outcomes_by_language.svg").write_text(outcomes_by_language(metrics), encoding="utf-8")
    (out / "consistency_histogram.svg").write_text(consistency_histogram(items, judgments), encoding="utf-8")
    print(f"wrote figures to {out}")


if __name__ == "__main__":
    main()
