#import "common.typ": *
#let d(x) = (if x >= 0 { "+" } else { "−" }) + str(calc.round(calc.abs(x) * 100, digits: 1))
#let acc = c.accuracy

*Paired tests.* Differences are Apertus minus Qwen in percentage points, with a 95% paired bootstrap over facts and an exact McNemar test on the items only one model gets right (no correction for multiple comparisons; borderline values should be read as indicative).

- *Romansh: Apertus ahead* (significant, but close to the threshold). #d(acc.rm.diff) pp (CI #d(acc.rm.ci95.at(0)) to #d(acc.rm.ci95.at(1)), McNemar p = #acc.rm.mcnemar_p\; #acc.rm.only_a_correct items only Apertus gets right vs. #acc.rm.only_b_correct only Qwen). Qwen also abstains much more in Romansh (#q.by_language.rm.not_attempted vs. #m.by_language.rm.not_attempted items), and its Romansh answers agree least with its other languages.
- *Consistency: Apertus ahead.* #c.consistency_at_4.a facts are answered correctly in all four languages by Apertus vs. #c.consistency_at_4.b by Qwen (p = #c.consistency_at_4.mcnemar_p).
- *German, French, Italian: no reliable difference* (#d(acc.de.diff), #d(acc.fr.diff), #d(acc.it.diff) pp; all CIs include zero). Overall: #d(acc.all.diff) pp (McNemar p = #acc.all.mcnemar_p, fact-level CI #d(acc.all.ci95.at(0)) to #d(acc.all.ci95.at(1))).
- *False premises: Qwen clearly ahead.* Apertus rejects the false premise less often (#d(c.false_premise.diff) pp, CI #d(c.false_premise.ci95.at(0)) to #d(c.false_premise.ci95.at(1)), p = #c.false_premise.mcnemar_p): Qwen corrects #c.false_premise.only_b_correct premises Apertus accepts, the reverse happens #c.false_premise.only_a_correct times.
- *The agreement signal transfers.* On Qwen, cross-lingual agreement predicts correctness with AUROC #calc.round(q.cross_lingual_signal.auroc, digits: 2) (Apertus #calc.round(m.cross_lingual_signal.auroc, digits: 2)), so Finding 6 is not specific to one model.

In short, Apertus' Swiss focus pays off exactly where it should, in Romansh and in giving the same answer across the national languages, while its weaker premise checking is a concrete target for alignment.
