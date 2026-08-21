import json
import os

def load_evaluation_dataset(file_path="data/eval/expected_results.json"):
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        if isinstance(data, dict):
            return list(data.values())
        elif isinstance(data, list):
            return data
        return []

def load_test_briefs(file_path="data/eval/test_briefs.md"):
    if not os.path.exists(file_path):
        return ""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()