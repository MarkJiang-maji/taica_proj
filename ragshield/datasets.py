from __future__ import annotations

import csv
import json
import urllib.parse
import urllib.request
from pathlib import Path

HF_ROWS_ENDPOINT = "https://datasets-server.huggingface.co/rows"


def fetch_hf_rows(dataset: str, split: str, length: int = 100, offset: int = 0) -> dict:
    query = urllib.parse.urlencode(
        {
            "dataset": dataset,
            "config": "default",
            "split": split,
            "offset": offset,
            "length": length,
        }
    )
    url = f"{HF_ROWS_ENDPOINT}?{query}"
    with urllib.request.urlopen(url, timeout=45) as response:
        return json.loads(response.read().decode("utf-8"))


def download_deepset_prompt_injections(output_dir: Path) -> Path:
    """Download the public deepset/prompt-injections rows as CSV.

    Uses the Hugging Face datasets-server API to avoid installing pyarrow or the
    datasets package on the shared machine.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "deepset_prompt_injections.csv"
    rows: list[dict[str, object]] = []
    for split in ("train", "test"):
        first = fetch_hf_rows("deepset/prompt-injections", split, length=100, offset=0)
        total = int(first["num_rows_total"])
        offset = 0
        while offset < total:
            payload = first if offset == 0 else fetch_hf_rows("deepset/prompt-injections", split, length=100, offset=offset)
            for row in payload["rows"]:
                rows.append(
                    {
                        "dataset": "deepset/prompt-injections",
                        "split": split,
                        "row_idx": row["row_idx"],
                        "text": row["row"]["text"],
                        "label": row["row"]["label"],
                    }
                )
            offset += 100
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["dataset", "split", "row_idx", "text", "label"])
        writer.writeheader()
        writer.writerows(rows)
    return output_path


def load_dataset_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))

