"""Render report figures as SVG (standard library only).

Usage: python -m swisscivicqa.figures results/metrics_X.json data/results/judgments_X.jsonl report/figures
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from .paths import project_root

ROOT = project_root()
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


def fact_matrix(items: dict, judgments: list) -> str:
    """One column per fact, one row per language; facts sorted by how many languages got them right."""
    label = {}
    for j in judgments:
        it = items[j["id"]]
        label[(it["fact_id"], it["language"])] = j["judge_label"]
    facts = sorted({f for f, _ in label},
                   key=lambda f: (-sum(label.get((f, l)) == "CORRECT" for l in LANGS), f))
    cell, gap, left, top = 4.6, 0.8, 70, 34
    w = left + len(facts) * (cell + gap) + 12
    h = top + len(LANGS) * (cell * 4 + 4) + 40
    color = {"CORRECT": C_CORRECT, "INCORRECT": C_INCORRECT, "NOT_ATTEMPTED": C_NA}
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w:.0f}' height='{h:.0f}' viewBox='0 0 {w:.0f} {h:.0f}'>",
           f"<rect width='{w:.0f}' height='{h:.0f}' fill='{SURFACE}'/>"]
    lx = left
    for name, col in [("Correct", C_CORRECT), ("Not attempted", C_NA), ("Incorrect", C_INCORRECT)]:
        out.append(f"<rect x='{lx}' y='10' width='12' height='12' rx='2' fill='{col}'/>")
        out.append(text(lx + 17, 20, name, 11, INK2))
        lx += 17 + len(name) * 6.4 + 22
    row_h = cell * 4
    for r, lang in enumerate(LANGS):
        y = top + r * (row_h + 4)
        out.append(text(left - 8, y + row_h / 2 + 4, LANG_LABEL[lang], 11, INK, "end"))
        for c, f in enumerate(facts):
            x = left + c * (cell + gap)
            out.append(f"<rect x='{x:.1f}' y='{y:.1f}' width='{cell:.1f}' height='{row_h:.1f}' fill='{color[label[(f, lang)]]}'/>")
    # boundaries between groups (4/4, 3/4, ...)
    counts = [sum(label[(f, l)] == "CORRECT" for l in LANGS) for f in facts]
    y_end = top + len(LANGS) * (row_h + 4)
    start = 0
    for c in range(1, len(facts) + 1):
        if c == len(facts) or counts[c] != counts[start]:
            mid = left + (start + c) / 2 * (cell + gap)
            out.append(text(mid, y_end + 12, f"{counts[start]}/4", 10, INK2, "middle"))
            if c < len(facts):
                x = left + c * (cell + gap) - gap / 2
                out.append(f"<line x1='{x:.1f}' x2='{x:.1f}' y1='{top - 4}' y2='{y_end + 2}' stroke='{INK}' stroke-width='0.8'/>")
            start = c
    out.append(text(left + (w - left) / 2, h - 6, f"{len(facts)} facts, grouped by number of languages answered correctly", 11, INK2, "middle"))
    out.append("</svg>")
    return "\n".join(out)


def model_comparison(models: dict) -> str:
    """Grouped bars: accuracy per language (+ consistency@4) for each model, with 95% CI whiskers."""
    groups = [(LANG_LABEL[l], l) for l in LANGS] + [("All 4 (consistency)", None)]
    names = list(models)
    cols = [C_CORRECT, "#1baf7a"]  # validated categorical slots 1 and 3 (blue, aqua)
    w, h, left, top, bottom = 620, 250, 44, 34, 40
    plot_w, plot_h = w - left - 16, h - top - bottom
    gw = plot_w / len(groups)
    bw = gw * 0.32
    out = [f"<svg xmlns='http://www.w3.org/2000/svg' width='{w}' height='{h}' viewBox='0 0 {w} {h}'>",
           f"<rect width='{w}' height='{h}' fill='{SURFACE}'/>"]
    lx = left
    for name, col in zip(names, cols):
        out.append(f"<rect x='{lx}' y='10' width='12' height='12' rx='2' fill='{col}'/>")
        out.append(text(lx + 17, 20, name, 11, INK2))
        lx += 17 + len(name) * 6.4 + 26
    for v in (0, 25, 50, 75):
        y = top + plot_h - plot_h * v / 75
        out.append(f"<line x1='{left}' x2='{w - 16}' y1='{y:.1f}' y2='{y:.1f}' stroke='{GRID}' stroke-width='1'/>")
        out.append(text(left - 6, y + 4, f"{v}%", 10, INK2, "end"))
    for g, (label, lang) in enumerate(groups):
        for k, name in enumerate(names):
            m = models[name]
            val = m["by_language"][lang]["accuracy"] if lang else m["cross_lingual"]["consistency_at_4"]
            x = left + g * gw + gw / 2 - bw - 1 + k * (bw + 2)
            bh = plot_h * val / 0.75
            y = top + plot_h - bh
            r = min(4, bh)
            out.append(f"<path d='M{x:.1f},{top + plot_h:.1f} V{y + r:.1f} Q{x:.1f},{y:.1f} {x + r:.1f},{y:.1f} "
                       f"H{x + bw - r:.1f} Q{x + bw:.1f},{y:.1f} {x + bw:.1f},{y + r:.1f} V{top + plot_h:.1f} Z' fill='{cols[k]}'/>")
            if lang:
                lo, hi = m["by_language"][lang]["accuracy_ci95"]
                y1, y2 = top + plot_h - plot_h * lo / 0.75, top + plot_h - plot_h * hi / 0.75
                cx = x + bw / 2
                out.append(f"<line x1='{cx:.1f}' x2='{cx:.1f}' y1='{y1:.1f}' y2='{y2:.1f}' stroke='{INK}' stroke-width='1'/>")
            out.append(text(x + bw / 2, min(y, top + plot_h - 2) - 5 if not lang else y2 - 4 if lang else y - 5,
                            f"{100 * val:.0f}", 10, INK, "middle"))
        out.append(text(left + g * gw + gw / 2, top + plot_h + 16, label, 11, INK2, "middle"))
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
    (out / "fact_matrix.svg").write_text(fact_matrix(items, judgments), encoding="utf-8")
    names = {"apertus-v1.5-8b-text-q8_0": "Apertus 1.5 8B", "qwen3-8b-q8_0": "Qwen3 8B (baseline)"}
    expected = {n: ROOT / "results" / "expected" / f"{n}.json" for n in names}
    if all(p.exists() for p in expected.values()):
        models = {names[n]: json.loads(p.read_text(encoding="utf-8")) for n, p in expected.items()}
        (out / "model_comparison.svg").write_text(model_comparison(models), encoding="utf-8")
    print(f"wrote figures to {out}")


if __name__ == "__main__":
    main()
