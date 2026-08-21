from src.security.guards import check_prompt_injection


def run_poisoned_brief_tests(test_cases):
    results = []
    for case in test_cases:
        is_poisoned = check_prompt_injection(case["content"])
        caught = (is_poisoned == case["expected_poison"])

        results.append({
            "test_id": case["id"],
            "caught": caught
        })
    return results


def calculate_poison_catch_rate(results):
    if not results:
        return 0.0

    caught_count = sum(1 for r in results if r["caught"])
    return (caught_count / len(results)) * 100