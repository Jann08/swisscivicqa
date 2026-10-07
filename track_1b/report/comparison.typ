#import "common.typ": *
// Baseline comparison; all numbers from results/expected/qwen3-8b-q8_0.json.
== Baseline: is the Swiss model better at Swiss facts?

To put the numbers in context we ran the identical pipeline (same items, prompts, decoding, judge) on *Qwen3 8B* (Q8_0, thinking disabled), an open model of the same size that was not trained with a Swiss focus.

#figure(image("figures/model_comparison.svg", width: 92%), caption: [Accuracy per language with 95% bootstrap CIs, and consistency\@4, for Apertus 1.5 8B and the Qwen3 8B baseline.]) <fig3>

#figure(
  table(columns: (auto, auto, auto),
    [Metric], [Apertus 1.5 8B], [Qwen3 8B],
    ..langs.map(l => (L.at(l) + " accuracy", pct(m.by_language.at(l).accuracy), pct(q.by_language.at(l).accuracy))).flatten(),
    [Consistency\@4], pct(m.cross_lingual.consistency_at_4), pct(q.cross_lingual.consistency_at_4),
    [Hallucination rate], pct(m.overall.hallucination_rate), pct(q.overall.hallucination_rate),
    [Not attempted], str(m.overall.not_attempted), str(q.overall.not_attempted),
    [False premise (mean)], pct(langs.map(l => m.by_type.false_premise.at(l)).sum() / 4), pct(langs.map(l => q.by_type.false_premise.at(l)).sum() / 4),
  ),
  caption: [Apertus vs. the Qwen3 8B baseline on SwissCivicQA-4L.]
)

#include "comparison_text.typ"
