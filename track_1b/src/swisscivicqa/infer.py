"""Query a model behind an OpenAI-compatible chat endpoint for every evaluation item.

Resumable: items already present in the output file are skipped.

Usage: python -m swisscivicqa.infer --base-url http://127.0.0.1:8088/v1 --model apertus-v1.5-8b \
           --out data/results/responses_apertus-v1.5-8b.jsonl
"""
import argparse
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Short, neutral instruction in the question's language; keeps answers gradeable
# without hinting at the answer.
INSTRUCTION = {
    "de": "Beantworte die folgende Frage zur Schweizer Bundesverfassung kurz und präzise.",
    "fr": "Réponds de manière brève et précise à la question suivante sur la Constitution fédérale suisse.",
    "it": "Rispondi in modo breve e preciso alla seguente domanda sulla Costituzione federale svizzera.",
    "rm": "Respunda curt e precis a la suandanta dumonda davart la Constituziun federala svizra.",
}
PARAMS = {"temperature": 0.0, "top_p": 1.0, "max_tokens": 256, "seed": 42}


def chat(base_url: str, model: str, prompt: str, retries: int = 3) -> dict:
    body = json.dumps({"model": model, "messages": [{"role": "user", "content": prompt}], **PARAMS}).encode()
    req = urllib.request.Request(f"{base_url}/chat/completions", data=body, headers={"Content-Type": "application/json"})
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=600) as r:
                return json.load(r)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(5 * (attempt + 1))
    raise RuntimeError("unreachable")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", default=str(ROOT / "data" / "dataset" / "eval.jsonl"))
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    items = [json.loads(l) for l in open(args.dataset, encoding="utf-8")]
    if args.limit:
        items = items[: args.limit]
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if out.exists():
        done = {json.loads(l)["id"] for l in open(out, encoding="utf-8") if l.strip()}
    with open(out, "a", encoding="utf-8") as fh:
        for n, item in enumerate(items, 1):
            if item["id"] in done:
                continue
            prompt = f"{INSTRUCTION[item['language']]}\n\n{item['question']}"
            t0 = time.time()
            resp = chat(args.base_url, args.model, prompt)
            fh.write(json.dumps({
                "id": item["id"],
                "model": args.model,
                "prompt": prompt,
                "response": resp["choices"][0]["message"]["content"],
                "finish_reason": resp["choices"][0].get("finish_reason"),
                "params": PARAMS,
                "latency_s": round(time.time() - t0, 2),
            }, ensure_ascii=False) + "\n")
            fh.flush()
            print(f"[{n}/{len(items)}] {item['id']} {time.time() - t0:.1f}s", flush=True)


if __name__ == "__main__":
    main()
