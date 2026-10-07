"""End-to-end entry point used by `make run`.

  verify (default): rebuild the dataset from the official text, run the tests, recompute all
                    metrics from the committed model responses / judgments / human review and
                    check them against results/expected/<model>.json. Needs no model or GPU.
  full:             additionally re-run inference and judging against OpenAI-compatible
                    endpoints (MODEL_URL, JUDGE_URL), e.g. the llama.cpp services in
                    docker-compose.full.yml. Works for any model: set MODEL_NAME.

Usage: python -m swisscivicqa.pipeline [verify|full]
"""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from .paths import project_root

from . import build, compare, pairs, parse, score, validate

ROOT = project_root()
RESULTS = ROOT / "results"
DEFAULT_MODEL = "apertus-v1.5-8b-text-q8_0"
DEFAULT_JUDGE = "gemma-3-12b-it-q4_k_m"


def step(msg: str) -> None:
    print(f"\n==> {msg}", flush=True)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_inputs() -> None:
    step("Checking official source files (SHA-256)")
    for line in (ROOT / "data" / "raw" / "SHA256SUMS").read_text().split("\n"):
        if line.strip():
            digest, name = line.split()
            if sha256(ROOT / "data" / "raw" / name) != digest:
                raise SystemExit(f"checksum mismatch: {name}")
    print("ok")
    step("Parsing constitution and validating every fact against the official text")
    parse.main(str(ROOT / "data" / "raw"), str(ROOT / "data" / "processed"))
    errors = validate.check(validate.load_facts())
    if errors:
        raise SystemExit("\n".join(errors))
    step("Building evaluation dataset")
    build.main()
    step("Running unit tests")
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), top_level_dir=str(ROOT / "tests"))
    if not unittest.TextTestRunner(verbosity=1).run(suite).wasSuccessful():
        raise SystemExit("tests failed")


def run_models(model: str, judge: str) -> None:
    model_url, judge_url = os.environ.get("MODEL_URL"), os.environ.get("JUDGE_URL")
    if not model_url or not judge_url:
        raise SystemExit("full mode needs MODEL_URL and JUDGE_URL (OpenAI-compatible /v1 endpoints)")
    responses = ROOT / "data" / "results" / f"responses_{model}.jsonl"
    step(f"Inference: {model}")
    subprocess.run([sys.executable, "-m", "swisscivicqa.infer", "--base-url", model_url, "--model", model,
                    "--out", str(responses)], check=True)
    step(f"Judging with {judge}")
    subprocess.run([sys.executable, "-m", "swisscivicqa.grade", "--responses", str(responses),
                    "--judge-url", judge_url, "--judge-model", judge], check=True)


def check_metrics(model: str) -> int:
    """Recompute metrics for one model and compare with results/expected/<model>.json if present."""
    step(f"Computing metrics: {model}")
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    jpath = ROOT / "data" / "results" / f"judgments_{model}.jsonl"
    judgments = [json.loads(l) for l in open(jpath, encoding="utf-8") if l.strip()]
    # The blind human audit was done on the reference model's responses only.
    hpath = ROOT / "data" / "human_review" / "review.jsonl"
    human = [json.loads(l) for l in open(hpath, encoding="utf-8")] if model == DEFAULT_MODEL and hpath.exists() else []
    rpath = ROOT / "data" / "results" / f"responses_{model}.jsonl"
    responses = {r["id"]: r["response"] for r in map(json.loads, open(rpath, encoding="utf-8"))} if rpath.exists() else {}
    metrics = score.compute(items, judgments, human, responses)
    ppath = ROOT / "data" / "results" / f"pairs_{model}.jsonl"
    if ppath.exists():
        labels = {j["id"]: j["judge_label"] for j in judgments}
        metrics["cross_lingual_signal_all_items"] = pairs.evaluate(
            items, [json.loads(l) for l in open(ppath, encoding="utf-8") if l.strip()], labels)
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / f"metrics_{model}.json").write_text(json.dumps(metrics, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{'lang':<5}{'acc':>7}{'CI95':>17}{'halluc.':>9}{'not att.':>10}")
    for lang, m in metrics["by_language"].items():
        print(f"{lang:<5}{m['accuracy']:>7.3f}  [{m['accuracy_ci95'][0]:.3f}, {m['accuracy_ci95'][1]:.3f}]"
              f"{m['hallucination_rate']:>9.3f}{m['not_attempted']:>10}")
    print("cross-lingual:", json.dumps(metrics["cross_lingual"]))
    print("judge vs rules:", json.dumps(metrics["judge_vs_rules"]))
    for key in ("cross_lingual_signal", "cross_lingual_signal_all_items", "judge_vs_human", "inter_annotator"):
        if key in metrics:
            print(f"{key.replace('_', ' ')}:", json.dumps(metrics[key]))
    expected = RESULTS / "expected" / f"{model}.json"
    if expected.exists():
        if json.loads(expected.read_text(encoding="utf-8")) != metrics:
            print(f"MISMATCH: recomputed metrics for {model} differ from {expected.relative_to(ROOT)}")
            return 1
        print(f"ok: identical to published {expected.relative_to(ROOT)}")
    return 0


BASELINE = "qwen3-8b-q8_0"


def check_comparison(models: list) -> int:
    """Paired comparison reference model vs. baseline, verified like the per-model metrics."""
    if DEFAULT_MODEL not in models or BASELINE not in models:
        return 0
    step(f"Paired comparison: {DEFAULT_MODEL} vs {BASELINE}")
    items = {i["id"]: i for i in map(json.loads, open(ROOT / "data" / "dataset" / "eval.jsonl", encoding="utf-8"))}
    a = compare.load_labels(ROOT / "data" / "results" / f"judgments_{DEFAULT_MODEL}.jsonl")
    b = compare.load_labels(ROOT / "data" / "results" / f"judgments_{BASELINE}.jsonl")
    fp = {i: it for i, it in items.items() if it["answer_type"] == "false_premise"}
    res = {"model_a": DEFAULT_MODEL, "model_b": BASELINE, "accuracy": compare.paired(items, a, b),
           "consistency_at_4": compare.consistency_diff(items, a, b), "false_premise": compare.paired(fp, a, b)["all"]}
    for scope, r in res["accuracy"].items():
        print(f"{scope:<4} diff {r['diff']:+.3f}  CI95 [{r['ci95'][0]:+.3f}, {r['ci95'][1]:+.3f}]  McNemar p={r['mcnemar_p']}")
    print("consistency@4:", json.dumps(res["consistency_at_4"]))
    print("false premise:", json.dumps(res["false_premise"]))
    expected = RESULTS / "expected" / "comparison.json"
    if expected.exists():
        if json.loads(expected.read_text(encoding="utf-8")) != res:
            print("MISMATCH: comparison differs from results/expected/comparison.json")
            return 1
        print("ok: identical to published results/expected/comparison.json")
    else:
        expected.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8")
    return 0


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    model = os.environ.get("MODEL_NAME", DEFAULT_MODEL)
    judge = os.environ.get("JUDGE_NAME", DEFAULT_JUDGE)
    verify_inputs()
    if mode == "full":
        run_models(model, judge)
    elif mode != "verify":
        raise SystemExit(f"unknown mode {mode}")
    models = sorted(p.stem.removeprefix("judgments_") for p in (ROOT / "data" / "results").glob("judgments_*.jsonl"))
    if mode == "full" and model not in models:
        models.append(model)
    failures = sum(check_metrics(m) for m in models)
    failures += check_comparison(models)
    step("Summary")
    print(f"{len(models)} model(s) verified, {failures} mismatch(es)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
