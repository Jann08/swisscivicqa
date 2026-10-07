# Technical report: SwissCivicQA-4L

> Citizens ask about their constitutional rights in their own national language. SwissCivicQA-4L asks 122 facts of the Swiss Federal Constitution in German, French, Italian and Romansh (488 items, incl. false-premise traps), each gold answer verbatim-grounded in the official text of the same language. Apertus 1.5 8B answers 45.1% correctly (43.4%–46.7% across languages), but only 23.8% of facts correctly in all four languages.

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

- 122 facts × 4 languages = 488 single-turn, closed-book items; 20 facts are false-premise questions.
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

Audit: (1) deterministic rules for number and yes/no items: judge–rule agreement 97.8% (κ = 0.9542, n = 138); (2) blind human review of a stratified 20% sample (n = 96) by two annotators: human–human agreement 88.5% (κ = 0.7833), judge–human agreement 86.5% (κ = 0.7392). The judge is slightly lenient (47.9% vs. 44.8% correct on the sample); human-calibrated overall accuracy ≈ 41.9%.

### Evaluation setup and inference parameters

llama.cpp server, temperature 0, top_p 1, seed 42, max 256 tokens, default chat template (`--jinja`), one short instruction in the question's language, no system prompt, no retrieval.

### Results

| Language | Accuracy | 95% CI | Correct given attempted | Hallucination | Not attempted |
|---|---|---|---|---|---|
| German | 43.4% | 34.4%–52.5% | 44.5% | 55.5% | 3 |
| French | 44.3% | 36.1%–53.3% | 45.0% | 55.0% | 2 |
| Italian | 46.7% | 38.5%–55.7% | 48.3% | 51.7% | 4 |
| Romansh | 45.9% | 36.9%–54.9% | 49.6% | 50.4% | 9 |

Consistency@4: **23.8%**; correct in at least one language: 68.0%; facts known somewhere but not everywhere: 54.

| Type | DE | FR | IT | RM |
|---|---|---|---|---|
| entity | 35.9% | 47.2% | 47.2% | 50.9% |
| false premise | 10.0% | 10.0% | 30.0% | 10.0% |
| list | 42.9% | 28.6% | 28.6% | 14.3% |
| number | 55.2% | 55.2% | 48.3% | 51.7% |
| yes no | 100.0% | 69.2% | 76.9% | 84.6% |

### Baseline: Qwen3 8B

Same items, prompts, decoding and judge; Qwen3-8B (Q8_0, thinking disabled) as a same-size, non-Swiss open model.

| Language | Apertus 1.5 8B | Qwen3 8B |
|---|---|---|
| German | 43.4% | 37.7% |
| French | 44.3% | 41.0% |
| Italian | 46.7% | 45.1% |
| Romansh | 45.9% | 34.4% |
| **Consistency@4** | 23.8% | 13.9% |
| Hallucination rate | 53.2% | 58.2% |
| False-premise accuracy (mean) | 15.0% | 32.5% |

See the PDF report for figures and discussion.

Cross-lingual agreement as a reference-free hallucination signal (number and yes/no items, n = 140): answers agreeing with all other languages are correct in 89.0%, answers agreeing with none in 21.4%; AUROC 0.81.
Extended to all 488 items (LLM-judged pairwise agreement, gold answer unseen): AUROC 0.73 (yes/no 0.89, number 0.74, entity 0.73, list 0.80; false premise 0.46, i.e. no signal: a premise accepted in every language agrees with itself).

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
