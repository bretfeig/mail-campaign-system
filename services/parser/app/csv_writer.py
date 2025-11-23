import csv
import os
from .config import CSV_HEADER, OUTPUT_CSV


def ensure_header(path: str = OUTPUT_CSV) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(CSV_HEADER)


def append_rows(rows: list[dict], path: str = OUTPUT_CSV) -> None:
    if not rows:
        return
    ensure_header(path)
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADER)
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in CSV_HEADER})

