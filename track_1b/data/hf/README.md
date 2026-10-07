---
license: cdla-permissive-2.0
language:
- de
- fr
- it
- rm
task_categories:
- question-answering
pretty_name: SwissCivicQA-4L
size_categories:
- n<1K
tags:
- switzerland
- constitution
- multilingual
- romansh
- factuality
- hallucination
- apertus
configs:
- config_name: eval
  data_files: eval.jsonl
- config_name: responses_apertus
  data_files: responses_apertus-v1.5-8b-text-q8_0.jsonl
- config_name: judgments_apertus
  data_files: judgments_apertus-v1.5-8b-text-q8_0.jsonl
- config_name: responses_qwen3_baseline
  data_files: responses_qwen3-8b-q8_0.jsonl
- config_name: judgments_qwen3_baseline
  data_files: judgments_qwen3-8b-q8_0.jsonl
- config_name: human_review
  data_files: human_review.jsonl
- config_name: metadata
  data_files: metadata.jsonl
---

# Dataset Card for SwissCivicQA-4L

Closed-book factual QA on the Swiss Federal Constitution (SR 101): 122 facts, each asked in German, French,
Italian and Romansh (488 items), including 20 false-premise facts. Built for Track 1B (Swiss Voices · Core Task
Intelligence) of the Online Hack Apertus 2026 to measure factuality, hallucination and **cross-lingual consistency**
of Apertus 1.5.

## Dataset Details

- **Curated by:** Team SwissCivicQA (Hack Apertus Online 2026)
- **Language(s) (NLP):** German (de, glottocode stan1295), French (fr, stan1290), Italian (it, ital1282), Romansh – Rumantsch Grischun (rm, roma1326)
- **License:** CDLA-Permissive-2.0 (dataset); the underlying constitutional text is not copyright-protected (Art. 5 para. 1 lit. a URG)
- **Git repository:** https://github.com/Jann08/swisscivicqa (directory `track_1b/`, `make run` reproduces every number)

## Uses

### Direct Use

Evaluating whether an LLM knows Swiss constitutional facts (popular rights, Federal Assembly, Federal Council,
courts, fundamental rights, federalism, taxes, social security) and knows them **equally in all four national
languages**; measuring hallucination and acceptance of false premises. Any OpenAI-compatible model can be evaluated
with the harness in the git repository.

### Out-of-Scope Use

Not legal advice and not a source of law: always consult the official text on fedlex.admin.ch. Not a measure of
legal reasoning (single-hop factual recall only), of cantonal law, or of spoken Swiss German dialects.

### Specifications

| | |
|---|---|
| Unit | one fact × one language = one single-turn question |
| Size | 122 facts × 4 languages = 488 items (20 false-premise facts = 80 items) |
| Answer types | number 29, entity 53, list 7, yes/no 13, false premise 20 (facts) |
| Ground truth | short gold answer + accepted variants, article/paragraph citation, verbatim evidence span in the same language |
| Source version | Federal Constitution, consolidated version of 2024-03-03 (in force), SHA-256 pinned |

## Dataset Structure

- `eval.jsonl` (test cases): `id` (`<fact>-<lang>`), `fact_id`, `language`, `question`, `gold_answer`, `gold_aliases`, `answer_type`, `category`, `source_citation`
- `responses_apertus-v1.5-8b-text-q8_0.jsonl` (model responses): `id`, `model`, `prompt`, `response`, `finish_reason`, `params`, `latency_s`
- `judgments_apertus-v1.5-8b-text-q8_0.jsonl`: `id`, `judge_model`, `judge_label`, `judge_raw`, `rule_label`
- `responses_qwen3-8b-q8_0.jsonl`, `judgments_qwen3-8b-q8_0.jsonl`: same format for the Qwen3 8B baseline (thinking disabled)
- `metadata.jsonl` (instance metadata): `id`, `article`, `paragraph`, `source_version`, `source_url`, `evidence_span`, `false_premise`, `license`, `license_note`, `contains_pii`, `authoring`, `glottocode`
- `human_review.jsonl`: blind human labels for the 20% audit sample (pseudonymous annotator ID)

## Dataset Creation

### Curation Rationale

Swiss citizens interact with the state in four national languages, and the Constitution exists in four official
versions. A sovereign, multilingual model should give the same correct answer regardless of the language of the
question. Existing factuality benchmarks do not test Swiss civic knowledge across all national languages, and
Romansh in particular is essentially untested.

### Source Data

The official HTML of the Federal Constitution on Fedlex (`https://www.fedlex.admin.ch/eli/cc/1999/404/20240303/{de,fr,it,rm}`),
downloaded on 2026-10-06; SHA-256 checksums are in the git repository.

#### Data Collection

1. Parse the four official versions to article/paragraph/letter level.
2. Select facts with one unambiguous answer stated in the text, covering all main areas of the Constitution; exclude Art. 127 (amended with effect from 2029-01-01).
3. Write a question per language using the official terminology of that language version; write gold answer and accepted variants.
4. For each language, record an evidence span copied from the cited paragraph that contains the answer.
5. Add 20 false-premise questions, each negating a fact that is itself in the dataset.

#### Source Data Producers and Data Subjects

The source text is produced by the Swiss Confederation (Federal Chancellery). There are no data subjects; the dataset contains no personal data.

#### Ownership and Consent Management

Official enactments are in the public domain (Art. 5 para. 1 lit. a URG). Questions, answer formulations and labels
are original work of the curators released under CDLA-Permissive-2.0. The human audit labels were produced by two adult volunteers who consented to publication under a pseudonymous ID and to their use for AI purposes; the consent form
template is `docs/consent_form_annotator.md` in the git repository.

#### Data Processing and Quality Control

- **Automated grounding check on every item:** the build fails unless each evidence span (≥ 8 characters) occurs verbatim (after whitespace/apostrophe normalisation) in the cited paragraph of the same language. All 488 items pass.
- **Stability check:** only provisions unchanged in the already adopted 2029 consolidation.
- **Integrity tests:** unique IDs, item count = facts × languages, parser tests (lettered and nested lists).
- **Reproducible build:** `python -m swisscivicqa.build` regenerates `eval.jsonl` byte-identically (SHA-256 recorded).

#### Data Instance Licenses

Every row of `metadata.jsonl` states `license: CDLA-Permissive-2.0` and a `license_note` on the public-domain status of the constitutional text.

### Annotations

#### Annotation Process

Gold answers are taken from the official text (no subjective annotation). Model responses were labelled
CORRECT / INCORRECT / NOT_ATTEMPTED by an LLM judge (gemma-3-12b-it Q4_K_M, SimpleQA grader template adapted for
language, lists and false premises), cross-checked by deterministic rules for number and yes/no items, and audited by
a blind human review of a stratified random 20% sample (24 items per language) by two annotators using the same written rubric.

#### Annotator Details

Two adult volunteer annotators (pseudonymous IDs `A1`, `A2`), each labelling the full 96-item sample independently
and blind to the judge labels. For French, Italian and Romansh items the parallel German question and answer were shown
alongside the official text. Annotation guidelines are part of the export (`src/swisscivicqa/review_sheet.py`).
Human–human agreement and judge–human agreement are reported in the technical report.

## Risks, Bias, and Limitations

- Questions in FR/IT/RM were drafted with AI assistance; their fluency may vary by language (gold answers are always grounded in the official text). Native-speaker review of the Romansh questions is the most important next step.
- The dataset covers federal constitutional facts only, single-hop recall, and the consolidated version of 2024-03-03.
- The constitutional text is in typical pre-training corpora; the benchmark measures recall of public knowledge, which is the intended use case.

### Personally Identifiable Information

None. Items contain only legal facts; human labels are linked to a pseudonymous annotator ID only.

### Sensitive Information

None.

### Recommendations

Report per-language accuracy *together with* cross-lingual consistency (share of facts correct in all four
languages); averages alone hide large item-level differences.

## Citations

**APA:** Team SwissCivicQA (2026). *SwissCivicQA-4L: cross-lingual factuality of LLMs on the Swiss Federal Constitution* [Data set]. Hack Apertus Online 2026.

## Dataset Card Authors

Team SwissCivicQA

## Dataset Card Contact

Via issues on https://github.com/Jann08/swisscivicqa
