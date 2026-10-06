// SwissCivicQA-4L technical report. All numbers are read from results/expected_metrics.json.
#import "common.typ": *

#set document(title: "SwissCivicQA-4L", author: "Team SwissCivicQA")
#set page(paper: "a4", margin: (x: 1.8cm, y: 1.6cm), numbering: "1 / 1")
#set text(font: ("Liberation Sans", "DejaVu Sans"), size: 9.5pt, lang: "en")
#set par(justify: true, leading: 0.55em, spacing: 0.75em)
#set heading(numbering: "1.")
#show heading.where(level: 1): it => block(above: 1.0em, below: 0.5em, text(size: 11.5pt, weight: "bold", it))
#show heading.where(level: 2): it => block(above: 0.8em, below: 0.4em, text(size: 10pt, weight: "bold", it))
#show table.cell.where(y: 0): set text(weight: "bold")
#set table(stroke: (x, y) => if y == 0 { (bottom: 0.6pt) } else { (bottom: 0.3pt + rgb("#e4e2dc")) }, inset: 4pt)

#align(center)[
  #text(size: 15pt, weight: "bold")[SwissCivicQA-4L]\
  #text(size: 11pt)[Does Apertus know the Swiss Federal Constitution equally well in all four national languages?]\
  #v(2pt)
  #text(size: 9pt, fill: ink2)[Hack Apertus Online 2026 · Track 1B Swiss Voices · Core Task Intelligence · Model: Apertus 1.5 8B]
]

#block(fill: rgb("#f3f2ee"), inset: 8pt, radius: 3pt, width: 100%)[
  *Summary.* Citizens ask about their constitutional rights in their own national language, and a "sovereign, multilingual" Swiss model should give the same correct answer in each. SwissCivicQA-4L is a closed-book factual QA set of #m.cross_lingual.facts facts from the Federal Constitution, each asked in German, French, Italian and Romansh (#m.overall.n items, incl. false-premise traps), with every gold answer verbatim-grounded in the official text of the same language. Apertus 1.5 8B answers #pct(m.overall.accuracy) of all items correctly, ranging from #pct(calc.min(..langs.map(l => m.by_language.at(l).accuracy))) to #pct(calc.max(..langs.map(l => m.by_language.at(l).accuracy))) across languages, and only #pct(m.cross_lingual.consistency_at_4) of facts are answered correctly in all four languages.
]

*Use of Apertus.* Model: `swiss-ai/Apertus-v1.5-8B` (text-only GGUF Q8_0 conversion `andreasmartin/apertus-v1.5-8b-text-Q8_0-GGUF`). Used for: evaluation. Runs on: local weights, llama.cpp CPU server (16 cores, no GPU).

= Use case

The Federal Constitution (SR 101) defines how Swiss direct democracy, federalism and fundamental rights work: how many signatures an initiative needs, who elects the Federal Council, which cantons have half a cantonal vote. These facts matter to every voter, are asked in four official versions of equal legal force (DE/FR/IT; RM for the Romansh-speaking population, Art. 70 para. 1), and change rarely, so a model can be expected to know them. A model that is right in German but wrong in Italian or Romansh fails exactly the users a *Swiss* model is meant to serve. The dataset therefore evaluates two things: *core task intelligence* (factuality and hallucination, SimpleQA-style) and *cross-lingual consistency* of that knowledge, which existing benchmarks do not test for Swiss civic knowledge and in particular not in Romansh.

= Dataset

== Specification

#table(columns: (auto, 1fr),
  [Item], [Specification],
  [Unit], [One fact asked in 4 languages (DE/FR/IT/RM, Rumantsch Grischun); single-turn, closed-book question],
  [Size], [#m.cross_lingual.facts facts × 4 = #m.overall.n items; 20 facts are false-premise questions (premise contradicts the Constitution)],
  [Answer types], [number, entity, list, yes/no, false-premise (see Table 2)],
  [Ground truth], [short gold answer + accepted variants per language, citation (article/paragraph), verbatim evidence span from the official text of *that* language],
  [Source], [Fedlex consolidated version 2024-03-03 (in force on 2026-10-16) in four languages, SHA-256 pinned; Art. 127 excluded (amended with effect from 2029)],
  [Files], [`eval.jsonl` (test cases) · `responses_*.jsonl` (model outputs) · `metadata.jsonl` (provenance, licence per item)],
)

== Construction and quality control

Facts were selected to cover all main areas of the Constitution (popular rights, Federal Assembly, Federal Council, courts, fundamental rights, languages, federalism, taxes, social security, transport) and to have one unambiguous answer stated in the text. Questions and translations were drafted with AI assistance and adapted to the official terminology of each language version (e.g. Romansh _Sursilvania/Sutsilvania_ for Obwalden/Nidwalden, _dumonda decisiva_ for the tie-break question). Quality is enforced mechanically, not by trust:

- *Evidence check (every item):* the validator parses the four official HTML files down to article/paragraph/letter and requires the item's evidence span (≥ 8 characters, containing the answer) to occur verbatim in the cited paragraph of the same language. The build fails on any miss; all #m.overall.n items pass.
- *Stability check:* only provisions unchanged between the version in force and the already adopted 2029 consolidation are used.
- *False-premise design:* each trap negates a fact that is itself in the dataset, so a model that "knows" the fact but accepts the premise is exposed.
- *No personal data:* items contain only legal facts; there are no data subjects.

== Licensing and provenance

Official enactments are not protected by copyright (Art. 5 para. 1 lit. a Swiss Copyright Act), so the gold answers can be redistributed freely; questions, answer formulations and labels are released under CDLA-Permissive-2.0. Every row of `metadata.jsonl` carries source URL, version, article, paragraph, evidence span, licence and an authoring note. The only human-generated data are the audit labels (Section 3.3); the annotator consent form is in `docs/consent_form_annotator.md`.

= Evaluation

== Setup

Inference: llama.cpp server (image pinned by digest), temperature 0, seed 42, max 256 tokens, default chat template of the GGUF (`--jinja`); no reasoning traces occur in any response. The prompt is one short instruction in the question's language ("answer briefly and precisely") followed by the question; no system prompt, no retrieval.

== Grading

Each response is labelled CORRECT / INCORRECT / NOT_ATTEMPTED with the SimpleQA grader template (adapted: language-aware, list and false-premise rules) by an open-weights judge, `gemma-3-12b-it` Q4_K_M, run locally (temperature 0). A different model family than the one under test is used to avoid self-preference. Metrics follow SimpleQA: accuracy, correct-given-attempted, hallucination rate = incorrect / attempted, F-score; 95% confidence intervals are percentile bootstraps over facts (2000 resamples, seed 42).

== Grading audit

Two independent checks: (1) *rules* — numbers and yes/no answers are graded deterministically (number normalisation incl. number words in all four languages); the judge agrees with the rules on #m.judge_vs_rules.n items with #pct(m.judge_vs_rules.agreement) agreement (Cohen's κ = #m.judge_vs_rules.cohen_kappa). (2) *human* — a stratified random 20% sample (#if "judge_vs_human" in m [#m.judge_vs_human.n] else [≈98] items, equal per language) was labelled *blind* (without seeing the judge label) by a native speaker of Swiss German with school French and Italian, using the same rubric and the official text side by side. #if "judge_vs_human" in m [Judge–human agreement: #pct(m.judge_vs_human.agreement), κ = #m.judge_vs_human.cohen_kappa.] else [_Human review pending._]

= Results

#figure(image("figures/outcomes_by_language.svg", width: 92%), caption: [Outcome distribution per language (#m.cross_lingual.facts items each). Bars sum to 100%.]) <fig1>

#figure(
  table(columns: (auto, auto, auto, auto, auto, auto),
    [Language], [Accuracy], [95% CI], [Correct | attempted], [Hallucination], [Not attempted],
    ..langs.map(l => {
      let b = m.by_language.at(l)
      (L.at(l), pct(b.accuracy), pct(b.accuracy_ci95.at(0)) + "–" + pct(b.accuracy_ci95.at(1)),
       pct(b.correct_given_attempted), pct(b.hallucination_rate), str(b.not_attempted))
    }).flatten()
  ),
  caption: [Main results, Apertus 1.5 8B (Q8_0).]
)

#grid(columns: (1fr, 1fr), gutter: 10pt,
  figure(image("figures/consistency_histogram.svg", width: 100%), caption: [Facts by number of languages answered correctly. Consistency\@4 = #pct(m.cross_lingual.consistency_at_4); known in ≥ 1 language: #pct(m.cross_lingual.any_at_4).]),
  figure(
    table(columns: (auto, auto, auto, auto, auto),
      [Type], ..langs.map(l => upper(l)),
      ..m.by_type.keys().map(t => (t.replace("_", " "), ..langs.map(l => pct(m.by_type.at(t).at(l))))).flatten()
    ),
    caption: [Accuracy by answer type and language.]
  ),
)

#include "findings.typ"

= Limitations

- *One model, one quantisation.* Results are for the 8B text-only Q8_0 conversion on llama.cpp; the 70B model and the original BF16 weights may differ. The harness accepts any OpenAI-compatible endpoint, so this is a one-line rerun.
- *Judge.* A 12B judge on four languages is imperfect, particularly for Romansh; this is why the grading is audited by rules and by humans and both agreements are reported.
- *Human audit.* One annotator; Romansh and Italian were judged against the official text rather than by a native speaker.
- *Translation of questions.* Questions in FR/IT/RM were written with AI assistance; wording quality may vary by language (answers are always grounded in the official text). A Romansh native-speaker review is the most valuable next step.
- *Contamination.* The Constitution is certainly in Apertus' pre-training data; the benchmark measures recall of in-distribution public knowledge, which is the point for this use case. The question formulations themselves are new.

= Lessons and recommendations

#include "lessons.typ"

= Reproducibility

`make run` (Docker, < 1 min, no model) re-parses the SHA-256-pinned sources, re-validates every evidence span, rebuilds the dataset, runs the unit tests, recomputes every number in this report from the committed responses, judgments and human labels and checks them against `results/expected_metrics.json`. `make full` downloads both GGUF files (SHA-256 checked), starts pinned llama.cpp containers and regenerates responses and judgments; `MODEL_NAME`/`MODEL_URL` evaluate any other model. Hardware used: 16-core x86 CPU, 32 GB RAM, no GPU.

*AI assistance.* Fact selection, question drafting, translations and code were produced with substantial help from an AI assistant (Claude, Anthropic); correctness is guaranteed by the mechanical evidence checks and audited by the human review. The model under test and the judge are open-weights models run locally.

*Licence.* Code Apache-2.0 · dataset CDLA-Permissive-2.0 · report and documentation CC-BY-4.0.

#text(size: 8.5pt, fill: ink2)[*References.* Wei et al. (2024), _Measuring short-form factuality in large language models_ (SimpleQA), arXiv:2411.04368 · Swiss AI Initiative (2025), _Apertus: Democratizing Open and Compliant LLMs_, arXiv:2509.14233 · Federal Constitution of the Swiss Confederation, SR 101, fedlex.admin.ch, version 2024-03-03.]
