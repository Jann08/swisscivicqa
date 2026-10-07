"""Render technical_report.md from the same metrics files as the Typst PDF (maintainer helper).

Usage: python scripts/render_md.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXP = ROOT / "results" / "expected"
LANGS = ("de", "fr", "it", "rm")
NAMES = {"de": "German", "fr": "French", "it": "Italian", "rm": "Romansh"}


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def main() -> None:
    m = json.loads((EXP / "apertus-v1.5-8b-text-q8_0.json").read_text(encoding="utf-8"))
    q_path = EXP / "qwen3-8b-q8_0.json"
    q = json.loads(q_path.read_text(encoding="utf-8")) if q_path.exists() else None
    h, ia = m["judge_vs_human"], m["inter_annotator"]
    accs = [m["by_language"][l]["accuracy"] for l in LANGS]
    calibrated = m["overall"]["accuracy"] - (h["judge_accuracy_on_sample"] - h["human_accuracy_on_sample"])

    rows = "\n".join(
        f"| {NAMES[l]} | {pct(b['accuracy'])} | {pct(b['accuracy_ci95'][0])}–{pct(b['accuracy_ci95'][1])} | "
        f"{pct(b['correct_given_attempted'])} | {pct(b['hallucination_rate'])} | {b['not_attempted']} |"
        for l, b in ((l, m["by_language"][l]) for l in LANGS))
    types = "\n".join(f"| {t.replace('_', ' ')} | " + " | ".join(pct(v[l]) for l in LANGS) + " |"
                      for t, v in m["by_type"].items())
    comparison = ""
    if q:
        comp_rows = "\n".join(
            f"| {NAMES[l]} | {pct(m['by_language'][l]['accuracy'])} | {pct(q['by_language'][l]['accuracy'])} |" for l in LANGS)
        comparison = f"""
### Baseline: Qwen3 8B

Same items, prompts, decoding and judge; Qwen3-8B (Q8_0, thinking disabled) as a same-size, non-Swiss open model.

| Language | Apertus 1.5 8B | Qwen3 8B |
|---|---|---|
{comp_rows}
| **Consistency@4** | {pct(m['cross_lingual']['consistency_at_4'])} | {pct(q['cross_lingual']['consistency_at_4'])} |
| Hallucination rate | {pct(m['overall']['hallucination_rate'])} | {pct(q['overall']['hallucination_rate'])} |
| False-premise accuracy (mean) | {pct(sum(m['by_type']['false_premise'].values()) / 4)} | {pct(sum(q['by_type']['false_premise'].values()) / 4)} |

See the PDF report for figures and discussion.
"""

    sg = m.get("cross_lingual_signal")
    signal = (f"Cross-lingual agreement as a reference-free hallucination signal (number and yes/no items, n = {sg['n']}): "
              f"answers agreeing with all other languages are correct in {pct(sg['agree_all']['p_correct'])}, answers agreeing "
              f"with none in {pct(sg['agree_none']['p_correct'])}; AUROC {sg['auroc']:.2f}.\n") if sg else ""
    md = f"""# Technical report: SwissCivicQA-4L

> Citizens ask about their constitutional rights in their own national language. SwissCivicQA-4L asks {m['cross_lingual']['facts']} facts of the Swiss Federal Constitution in German, French, Italian and Romansh ({m['overall']['n']} items, incl. false-premise traps), each gold answer verbatim-grounded in the official text of the same language. Apertus 1.5 8B answers {pct(m['overall']['accuracy'])} correctly ({pct(min(accs))}–{pct(max(accs))} across languages), but only {pct(m['cross_lingual']['consistency_at_4'])} of facts correctly in all four languages.

**Track:** Apertus Readiness - Track 1B (Swiss Voices · Core Task Intelligence)
**Event:** Online
**Team:** SwissCivicQA (solo submission; two volunteer annotators A1, A2)
**Demo:** `make run` (Docker, < 1 min) · PDF: `SwissCivicQA_Report.pdf`

----

### Use of Apertus

- **Model:** `swiss-ai/Apertus-v1.5-8B` (text-only GGUF Q8_0 conversion `andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF`)
- **How it is used:** evaluation
- **Where it runs:** local weights, llama.cpp CPU server (16 cores, no GPU), image pinned by digest

----
## Use Case Description

The Federal Constitution (SR 101) defines how Swiss direct democracy, federalism and fundamental rights work, and exists in four official language versions. A model that knows a provision in German but not in Italian or Romansh fails the users a sovereign Swiss model is meant to serve. The dataset measures core task intelligence (factuality and hallucination, SimpleQA-style) and the cross-lingual consistency of that knowledge, which has not been tested for Swiss civic knowledge, in particular not in Romansh.

## Dataset Summary

- {m['cross_lingual']['facts']} facts × 4 languages = {m['overall']['n']} single-turn, closed-book items; 20 facts are false-premise questions.
- Answer types: number, entity, list, yes/no, false premise. Categories cover popular rights, Federal Assembly, Federal Council, judiciary, fundamental rights, languages, federalism, taxes, social security, transport.
- Each item: question, gold answer + accepted variants, article/paragraph citation, verbatim evidence span from the official text of the same language, licence, source URL.
- Source: Fedlex consolidated version 2024-03-03 (in force), SHA-256 pinned; Art. 127 excluded (amended with effect from 2029).

## Data Collection Method

Facts with one unambiguous answer stated in the text were selected across all main areas. Questions and translations were drafted with AI assistance (Claude) and adapted to the official terminology of each language version. Quality is enforced mechanically: the build parses the four official HTML files to article/paragraph/letter level and fails unless every evidence span (≥ 8 characters, containing the answer) occurs verbatim in the cited paragraph of the same language. No data was collected from human subjects; the only human data are audit labels, produced with consent (`docs/consent_form_annotator.md`).

## Dataset Details

Official enactments are not copyright-protected (Art. 5 para. 1 lit. a URG). Questions, answer formulations and labels: CDLA-Permissive-2.0, with instance-level licence and provenance in `metadata.jsonl`. No personal data.

## Evaluation

### Method

SimpleQA three-way grading (CORRECT / INCORRECT / NOT_ATTEMPTED) by an open-weights judge (`gemma-3-12b-it` Q4_K_M, local; different model family than the model under test), with adapted rules for lists and false premises. Metrics: accuracy, correct-given-attempted, hallucination rate, F-score; consistency@4 (fact correct in all four languages); 95% bootstrap CIs over facts.

Audit: (1) deterministic rules for number and yes/no items: judge–rule agreement {pct(m['judge_vs_rules']['agreement'])} (κ = {m['judge_vs_rules']['cohen_kappa']}, n = {m['judge_vs_rules']['n']}); (2) blind human review of a stratified 20% sample (n = {h['n']}) by two annotators: human–human agreement {pct(ia['agreement'])} (κ = {ia['cohen_kappa']}), judge–human agreement {pct(h['agreement'])} (κ = {h['cohen_kappa']}). The judge is slightly lenient ({pct(h['judge_accuracy_on_sample'])} vs. {pct(h['human_accuracy_on_sample'])} correct on the sample); human-calibrated overall accuracy ≈ {pct(calibrated)}.

### Evaluation setup and inference parameters

llama.cpp server, temperature 0, top_p 1, seed 42, max 256 tokens, default chat template (`--jinja`), one short instruction in the question's language, no system prompt, no retrieval.

### Results

| Language | Accuracy | 95% CI | Correct given attempted | Hallucination | Not attempted |
|---|---|---|---|---|---|
{rows}

Consistency@4: **{pct(m['cross_lingual']['consistency_at_4'])}**; correct in at least one language: {pct(m['cross_lingual']['any_at_4'])}; facts known somewhere but not everywhere: {m['cross_lingual']['known_somewhere_but_not_everywhere']}.

| Type | DE | FR | IT | RM |
|---|---|---|---|---|
{types}
{comparison}
{signal}
Key findings: equal per-language averages hide large item-level inconsistency; the model almost never abstains; false premises are usually accepted, with language-specific inventions (e.g. a death penalty for treason and a non-existent constitutional court in French and Romansh); simple composition facts are robust while procedural thresholds fail.

## Dataset Limitations

One model size and quantisation; LLM judge imperfect (audited); two non-native annotators for FR/IT/RM; questions in FR/IT/RM drafted with AI assistance; the constitution is in pre-training data (recall of public knowledge is the intended use case).

## Lessons Learnt and Recommendations

Report consistency@4 alongside per-language accuracy; train calibrated abstention for civic facts; use the four parallel official versions for cross-lingual alignment data; add premise checking; next iteration: native-speaker review (especially Romansh), stricter judge prompt, cantonal constitutions, 70B model.

## Reproducibility

`make run` (Docker, < 1 min, no model, no GPU, no API key) re-parses the SHA-256-pinned sources, re-validates every evidence span, rebuilds the dataset, runs the unit tests and recomputes every number from the committed responses, judgments and human labels, checking them against `results/expected/`. `make full` re-runs inference and judging with pinned llama.cpp containers and SHA-256-checked GGUF files. CI runs `make run` on every commit. Hardware: 16-core x86 CPU, 32 GB RAM.

AI assistance: fact selection, question drafting, translations and code were produced with substantial help from Claude (Anthropic).

## License

Creative Commons Attribution 4.0 (CC-BY-4.0). All HackApertus projects are open-sourced.

## References

Wei et al. (2024), *Measuring short-form factuality in large language models* (SimpleQA), arXiv:2411.04368 · Swiss AI Initiative (2025), *Apertus: Democratizing Open and Compliant LLMs*, arXiv:2509.14233 · Federal Constitution of the Swiss Confederation, SR 101, fedlex.admin.ch, version 2024-03-03.
"""
    (ROOT / "technical_report.md").write_text(md, encoding="utf-8")
    print("wrote technical_report.md")


if __name__ == "__main__":
    main()
