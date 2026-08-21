def calculate_approval_within_n(results, n=3):
    if not results:
        return 0.0
    approved_within_n = sum(1 for r in results if r.get("cycles", 0) <= n and r.get("status") == "approved")
    return (approved_within_n / len(results)) * 100


def calculate_average_revision_cycles(results):
    if not results:
        return 0.0
    total_cycles = sum(r.get("cycles", 0) for r in results)
    return total_cycles / len(results)


def calculate_style_violation_catch_rate(results):
    if not results:
        return 0.0
    total_violations_present = sum(r.get("planted_violations", 0) for r in results)
    total_violations_caught = sum(r.get("caught_violations", 0) for r in results)

    if total_violations_present == 0:
        return 100.0

    return (total_violations_caught / total_violations_present) * 100