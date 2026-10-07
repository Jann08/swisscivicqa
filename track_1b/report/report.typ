// SwissCivicQA-4L technical report. All numbers are read from results/expected/<model>.json.
#import "common.typ": *

#set document(title: "SwissCivicQA-4L", author: "Team SwissCivicQA")
#set page(paper: "a4", margin: (x: 2cm, top: 2cm, bottom: 1.8cm),
  header: context if here().page() > 1 [
    #set text(font: sans, size: 7.5pt, fill: ink2)
    SwissCivicQA-4L #h(1fr) Hack Apertus 2026 · Track 1B
    #v(-6pt) #line(length: 100%, stroke: 0.4pt + rule)
  ],
  footer: context [
    #set text(font: sans, size: 7.5pt, fill: ink2)
    #h(1fr) #counter(page).display("1 / 1", both: true)
  ])
#set text(font: ("Libertinus Serif", "Liberation Serif"), size: 10.5pt, lang: "en", hyphenate: true)
#set par(justify: true, leading: 0.62em, spacing: 0.95em)
#set list(indent: 2pt, body-indent: 6pt, spacing: 0.7em, marker: text(fill: accent, "▸"))
#set heading(numbering: "1.")
#show heading.where(level: 1): it => block(above: 1.5em, below: 0.75em, width: 100%)[
  #set text(font: sans, size: 13pt, weight: "bold")
  #text(fill: accent, counter(heading).display()) #h(4pt) #it.body
  #v(-7pt) #line(length: 100%, stroke: 0.5pt + rule)
]
#show heading.where(level: 2): it => block(above: 1.1em, below: 0.55em,
  text(font: sans, size: 10.5pt, weight: "bold", [#text(fill: accent, counter(heading).display()) #h(3pt) #it.body]))
#show raw: set text(size: 8.5pt)
#show figure.caption: set text(font: sans, size: 8pt, fill: ink2)
#show figure: set block(above: 1.1em, below: 1.1em)
#show table.cell.where(y: 0): set text(font: sans, weight: "bold", size: 8.5pt)
#show table.cell: set text(size: 9pt)
#set table(stroke: (x, y) => if y == 0 { (bottom: 0.8pt + ink2) } else { (bottom: 0.3pt + rule) },
  fill: (x, y) => if y > 0 and calc.even(y) { paper2 } else { none }, inset: (x: 6pt, y: 4.5pt))
#show footnote.entry: set text(size: 8pt)

#block(width: 100%, below: 1.2em)[
  #box(width: 28pt, height: 4pt, fill: accent)
  #v(4pt)
  #text(font: sans, size: 24pt, weight: "bold")[SwissCivicQA-4L]
  #v(-8pt)
  #text(size: 13pt, style: "italic")[Does Apertus know the Swiss Federal Constitution equally well in all four national languages?]
  #v(2pt)
  #text(font: sans, size: 8.5pt, fill: ink2)[Hack Apertus Online 2026 #h(4pt)·#h(4pt) Track 1B Swiss Voices · Core Task Intelligence #h(4pt)·#h(4pt) Model: Apertus 1.5 8B]
]

#grid(columns: (1fr, 1fr, 1fr, 1fr), gutter: 6pt,
  stat(pct(m.overall.accuracy), [of #m.overall.n items answered correctly]),
  stat(pct(m.cross_lingual.consistency_at_4), [of facts correct in all four languages]),
  stat(pct(m.overall.hallucination_rate), [of attempted answers are wrong]),
  stat(str(calc.round(m.cross_lingual_signal.auroc, digits: 2)), [AUROC of cross-lingual agreement as hallucination detector]),
)
#v(4pt)

#block(fill: paper2, inset: 10pt, radius: 3pt, width: 100%)[
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

Two independent checks. (1) *Rules:* numbers and yes/no answers are graded deterministically (number normalisation incl. number words in all four languages); the judge agrees with the rules on #m.judge_vs_rules.n items with #pct(m.judge_vs_rules.agreement) agreement (Cohen's κ = #m.judge_vs_rules.cohen_kappa). (2) *Humans:* a stratified random 20% sample (#m.judge_vs_human.n items, 24 per language) was labelled *blind*, i.e. without seeing the judge label, by two adult volunteer annotators (pseudonymous IDs #m.judge_vs_human.annotators.join(", ")), using the same written rubric with the official text and the parallel German item shown side by side. Human–human agreement is #pct(m.inter_annotator.agreement) (κ = #m.inter_annotator.cohen_kappa); the judge agrees with the human consensus#footnote[Majority label; on the #(m.inter_annotator.n - calc.round(m.inter_annotator.agreement * m.inter_annotator.n)) items where the two annotators disagree, the label of A1 is used.] in #pct(m.judge_vs_human.agreement) of items (κ = #m.judge_vs_human.cohen_kappa), i.e. close to human level. Per language: #langs.map(l => upper(l) + " " + pct(m.judge_vs_human.by_language.at(l))).join(", ").

*Judge bias.* The judge is slightly lenient: on the sample it rates #pct(m.judge_vs_human.judge_accuracy_on_sample) of answers correct, the humans #pct(m.judge_vs_human.human_accuracy_on_sample). In 7 of the 9 items where both annotators disagree with the judge, the judge accepted an answer that adds a wrong claim, e.g. "a two-thirds majority of both chambers" for declaring a law urgent (Art. 165: majority of the members), or an answer to a false-premise question that does not correct the premise. Five of these nine are French, which explains the lower French agreement. A human-calibrated estimate of overall accuracy is therefore #pct(m.overall.accuracy - (m.judge_vs_human.judge_accuracy_on_sample - m.judge_vs_human.human_accuracy_on_sample)) instead of #pct(m.overall.accuracy); all conclusions below hold under both.

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

#figure(image("figures/fact_matrix.svg", width: 100%), caption: [Every fact (column) in every language (row). Only the left block is correct in all four languages: consistency\@4 = #pct(m.cross_lingual.consistency_at_4), while #pct(m.cross_lingual.any_at_4) of facts are answered correctly in at least one language.]) <fig2>

#align(center, figure(
    table(columns: (auto, auto, auto, auto, auto),
      [Type], ..langs.map(l => upper(l)),
      ..m.by_type.keys().map(t => (t.replace("_", " "), ..langs.map(l => pct(m.by_type.at(t).at(l))))).flatten()
    ),
    caption: [Accuracy by answer type and language.]
  ))

#include "findings.typ"

#include "comparison.typ"

= Limitations

- *Model scope.* Apertus 1.5 8B (text-only Q8_0 on llama.cpp) and one same-size baseline; the 70B model and the original BF16 weights may differ. The harness accepts any OpenAI-compatible endpoint, so this is a one-line rerun.
- *Judge.* A 12B judge on four languages is imperfect, particularly for Romansh; this is why the grading is audited by rules and by humans and both agreements are reported.
- *Human audit.* Two volunteer annotators on a 20% sample; Romansh items were judged against the official text and the parallel German item, not by native Romansh speakers.
- *Translation of questions.* Questions in FR/IT/RM were written with AI assistance; wording quality may vary by language (answers are always grounded in the official text). A Romansh native-speaker review is the most valuable next step.
- *Contamination.* The Constitution is certainly in Apertus' pre-training data; the benchmark measures recall of in-distribution public knowledge, which is the point for this use case. The question formulations themselves are new.

= Lessons and recommendations

#include "lessons.typ"

= Reproducibility

`make run` (Docker, < 1 min, no model) re-parses the SHA-256-pinned sources, re-validates every evidence span, rebuilds the dataset, runs the unit tests, recomputes every number in this report from the committed responses, judgments and human labels and checks them against `results/expected/<model>.json`. `make full` downloads both GGUF files (SHA-256 checked), starts pinned llama.cpp containers and regenerates responses and judgments; `MODEL_NAME`/`MODEL_URL` evaluate any other model. A GitHub Actions workflow runs `make run` on a clean runner for every commit, and the harness is a dependency-free, pip-installable package (`pip install ./track_1b`, Python ≥ 3.10, CLI `swisscivicqa verify`). Hardware used: 16-core x86 CPU, 32 GB RAM, no GPU.

*AI assistance.* Fact selection, question drafting, translations and code were produced with substantial help from an AI assistant (Claude, Anthropic); correctness is guaranteed by the mechanical evidence checks and audited by the human review. The model under test and the judge are open-weights models run locally.

*Licence.* Code Apache-2.0 · dataset CDLA-Permissive-2.0 · report and documentation CC-BY-4.0.

#text(size: 8.5pt, fill: ink2)[*References.* Wei et al. (2024), _Measuring short-form factuality in large language models_ (SimpleQA), arXiv:2411.04368 · Swiss AI Initiative (2025), _Apertus: Democratizing Open and Compliant LLMs_, arXiv:2509.14233 · Federal Constitution of the Swiss Confederation, SR 101, fedlex.admin.ch, version 2024-03-03.]
