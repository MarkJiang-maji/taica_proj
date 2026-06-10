from __future__ import annotations

from pathlib import Path

from .datasets import download_deepset_prompt_injections, load_dataset_csv
from .detector import detect_prompt_injection


def benchmark_detector(data_dir: Path) -> dict:
    dataset_path = data_dir / "deepset_prompt_injections.csv"
    if not dataset_path.exists():
        dataset_path = download_deepset_prompt_injections(data_dir)
    rows = load_dataset_csv(dataset_path)

    metrics = {
        "dataset": "deepset/prompt-injections",
        "dataset_path": str(dataset_path),
        "num_rows": len(rows),
        "true_positive": 0,
        "false_positive": 0,
        "true_negative": 0,
        "false_negative": 0,
        "examples": [],
    }

    for row in rows:
        label = int(row["label"])
        detection = detect_prompt_injection(row["text"])
        predicted = 1 if detection.is_injection else 0
        if label == 1 and predicted == 1:
            metrics["true_positive"] += 1
        elif label == 0 and predicted == 1:
            metrics["false_positive"] += 1
        elif label == 0 and predicted == 0:
            metrics["true_negative"] += 1
        elif label == 1 and predicted == 0:
            metrics["false_negative"] += 1
        if len(metrics["examples"]) < 12 and (label != predicted or detection.score >= 50):
            metrics["examples"].append(
                {
                    "split": row["split"],
                    "label": label,
                    "predicted": predicted,
                    "score": detection.score,
                    "level": detection.level,
                    "categories": detection.categories,
                    "text": row["text"][:280],
                }
            )

    tp = metrics["true_positive"]
    fp = metrics["false_positive"]
    tn = metrics["true_negative"]
    fn = metrics["false_negative"]
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    accuracy = (tp + tn) / max(1, len(rows))
    metrics.update(
        {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "accuracy": round(accuracy, 4),
        }
    )
    return metrics

