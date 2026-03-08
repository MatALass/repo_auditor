import csv
from pathlib import Path


def bootstrap_review_queue(path: Path):
    rows = []

    with path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            row["expected_repo_type"] = row["repo_type_detected"]
            row["expected_decision"] = row["decision_detected"]
            row["review_status"] = "auto"
            rows.append(row)

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    import sys

    path = Path(sys.argv[1])
    bootstrap_review_queue(path)

    print("Review queue bootstrapped.")