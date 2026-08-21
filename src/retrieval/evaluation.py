from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path

# Ensures project root is on sys.path when run directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.retrieval.retrieve import KBRetriever

def load_eval_set(path: str | Path) -> list[dict]:
    path = Path(path)
    if path.suffix == ".json":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
            return data.get("test_cases", data)
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]

def run_evaluation(
    eval_set_path: str | Path = "data/eval/retrieval_eval_set.jsonl",
    k_rules: int = 4,
    k_examples: int = 3,
    report_path: str | Path = "reports/retrieval_eval_results.md",
) -> str:
    retriever = KBRetriever()
    cases = load_eval_set(eval_set_path)

    rows = []
    rule_hits = example_hits = poisoned_leaks = 0

    for case in cases:
        payload = retriever.retrieve(
            brief_text=case["query"],
            content_type=case["content_type"],
            k_rules=k_rules,
            k_examples=k_examples,
        )
        retrieved_rule_ids = {c.id for c in payload.style_rules}
        retrieved_example_ids = {c.id for c in payload.similar_examples}

        rule_hit = bool(set(case["expected_style_rule_ids"]) & retrieved_rule_ids)
        example_hit = (
            not case["expected_example_ids"]
            or bool(set(case["expected_example_ids"]) & retrieved_example_ids)
        )
        leaked = any(c.poisoned for c in payload.similar_examples + payload.style_rules)

        rule_hits += rule_hit
        example_hits += example_hit
        poisoned_leaks += leaked

        rows.append(
            {
                "query": case["query"],
                "content_type": case["content_type"],
                "rule_hit": rule_hit,
                "example_hit": example_hit,
                "retrieved_rule_ids": sorted(retrieved_rule_ids),
                "retrieved_example_ids": sorted(retrieved_example_ids),
                "poisoned_leak": leaked,
            }
        )

    n = len(cases)
    rule_hit_rate = rule_hits / n if n else 0
    example_hit_rate = example_hits / n if n else 0

    report_lines = [
        "# Retrieval Evaluation Results",
        "",
        f"- Cases: {n}",
        f"- Style-rule hit rate (expected section in top-{k_rules}): "
        f"**{rule_hit_rate:.0%}** ({rule_hits}/{n})",
        f"- Example hit rate (expected example in top-{k_examples}): "
        f"**{example_hit_rate:.0%}** ({example_hits}/{n})",
        f"- Poisoned-content leaks in normal-mode retrieval: **{poisoned_leaks}** (target: 0)",
        "",
        "| Query | Content Type | Rule Hit | Example Hit | Retrieved Rule IDs | Retrieved Example IDs |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        report_lines.append(
            f"| {r['query'][:60]}{'…' if len(r['query']) > 60 else ''} | {r['content_type']} | "
            f"{'✅' if r['rule_hit'] else '❌'} | {'✅' if r['example_hit'] else '❌'} | "
            f"{', '.join(i.split('::')[-1] for i in r['retrieved_rule_ids'])} | "
            f"{', '.join(r['retrieved_example_ids'])} |"
        )

    report = "\n".join(report_lines) + "\n"
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).write_text(report, encoding="utf-8")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--eval-set", default="data/eval/retrieval_eval_set.jsonl")
    parser.add_argument("--k-rules", type=int, default=4)
    parser.add_argument("--k-examples", type=int, default=3)
    parser.add_argument("--report-path", default="reports/retrieval_eval_results.md")
    args = parser.parse_args()

    output = run_evaluation(args.eval_set, args.k_rules, args.k_examples, args.report_path)
    print(output)
    print(f"Report written to {args.report_path}")