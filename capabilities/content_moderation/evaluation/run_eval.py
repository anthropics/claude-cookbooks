"""End-to-end evaluation across all domains.

For each domain under ../data/:
  1. Get rules. ad_creatives uses the hand-written golden ruleset; other domains are
     compiled from their policies.md by Claude (cached in ./compiled/<domain>.json;
     delete the cache to force a fresh compile).
  2. Extract fields for every sample in samples.jsonl (one Claude call each; vision
     when the sample has an image).
  3. Evaluate deterministically and compare the decision to the sample's expected label.

Writes results.json and prints a per-domain table.

Run from capabilities/content_moderation/:   python evaluation/run_eval.py
Requires an Anthropic API key in ANTHROPIC_API_KEY (a .env file next to this script works too).
"""

import json
import pathlib
import sys

from dotenv import load_dotenv

load_dotenv()

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT))

from engine import evaluate, validate_document  # noqa: E402
from pipeline import compile_policies, extract_fields  # noqa: E402

COMPILED = HERE / "compiled"
COMPILED.mkdir(exist_ok=True)

DOMAINS = ["ad_creatives", "product_listings", "ugc"]


def load_domain(name: str) -> dict:
    d = ROOT / "data" / name
    return {
        "dir": d,
        "schema": json.loads((d / "schema.json").read_text()),
        "context": json.loads((d / "context.json").read_text()),
        "policies": (d / "policies.md").read_text(),
        "samples": [
            json.loads(line)
            for line in (d / "samples.jsonl").read_text().splitlines()
            if line.strip()
        ],
    }


def rules_for(name: str, dom: dict) -> dict:
    if name == "ad_creatives":
        return json.loads((dom["dir"] / "rules.golden.json").read_text())
    cache = COMPILED / f"{name}.json"
    if cache.exists():
        return json.loads(cache.read_text())
    print(f"  compiling {name} policies with Claude…")
    doc, attempts = compile_policies(dom["policies"], dom["schema"], dom["context"])
    print(
        f"  compiled in {len(attempts)} round(s): {len(doc['rules'])} rules, "
        f"{len(doc.get('derived_fields', {}))} derived, {len(doc.get('uncompilable', []))} uncompilable"
    )
    cache.write_text(json.dumps(doc, indent=2))
    return doc


def main() -> None:
    results = {"domains": {}, "totals": {"correct": 0, "n": 0}}
    for name in DOMAINS:
        dom = load_domain(name)
        doc = rules_for(name, dom)
        problems = validate_document(doc, dom["schema"], dom["context"])
        if problems:
            raise ValueError(f"{name}: ruleset fails static validation: {problems}")

        print(f"\n═══ {name} — {len(doc['rules'])} rules, {len(dom['samples'])} samples")
        rows = []
        for s in dom["samples"]:
            image = dom["dir"] / s["image"] if s.get("image") else None
            fields = extract_fields(
                s["submission"], dom["schema"], doc.get("derived_fields", {}), image_path=image
            )
            verdict = evaluate(doc["rules"], fields, s["context"])
            ok = verdict.decision == s["expected"]
            rows.append(
                {
                    "name": s["name"],
                    "expected": s["expected"],
                    "got": verdict.decision,
                    "ok": ok,
                    "fired": [r.rule_id for r in verdict.fired],
                    "unknown": [r.rule_id for r in verdict.unknown],
                }
            )
            mark = "✓" if ok else "✗"
            print(
                f"  {mark} {s['name']:<38} expected {s['expected']:<12} got {verdict.decision:<12} "
                f"fired: {', '.join(r.rule_id for r in verdict.fired) or '—'}"
            )
        correct = sum(r["ok"] for r in rows)
        results["domains"][name] = {"rows": rows, "correct": correct, "n": len(rows)}
        results["totals"]["correct"] += correct
        results["totals"]["n"] += len(rows)
        print(f"  → {correct}/{len(rows)} decisions correct")

    t = results["totals"]
    print(
        f"\n═══ TOTAL: {t['correct']}/{t['n']} decisions correct "
        f"({100 * t['correct'] / t['n']:.0f}%)"
    )
    (HERE / "results.json").write_text(json.dumps(results, indent=2))
    print(f"results written to {HERE / 'results.json'}")


if __name__ == "__main__":
    main()
