from src.evals.dataset import load_evaluation_dataset
from src.evals.metrics import (
    calculate_approval_within_n,
    calculate_average_revision_cycles,
    calculate_style_violation_catch_rate
)


def run_evaluations():
    dataset = load_evaluation_dataset()

    metrics = {
        "approval_within_n": calculate_approval_within_n(dataset, n=3),
        "average_revision_cycles": calculate_average_revision_cycles(dataset),
        "style_violation_catch_rate": calculate_style_violation_catch_rate(dataset)
    }

    return metrics


if __name__ == "__main__":
    results = run_evaluations()
    print(results)