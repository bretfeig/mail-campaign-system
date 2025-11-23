from __future__ import annotations
import argparse
import os
from glob import glob

from .csv_writer import append_rows, ensure_header
from .ingest_eml import parse_eml_bytes
from .config import OUTPUT_CSV


def run_scan_dir(scan_dir: str, once: bool = True) -> int:
    ensure_header(OUTPUT_CSV)
    pattern = os.path.join(scan_dir, "*.eml")
    files = sorted(glob(pattern))
    processed = 0
    for path in files:
        try:
            with open(path, "rb") as f:
                data = f.read()
            out = parse_eml_bytes(data)
            append_rows(out.get("rows", []), OUTPUT_CSV)
            processed += 1
        except Exception as e:
            print(f"WARN: failed to process {path}: {e}")
    print(f"Processed {processed} messages from {scan_dir}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Reply parser service")
    ap.add_argument("--scan-dir", default=None, help="Directory of .eml files to process (test mode)")
    ap.add_argument("--once", action="store_true", help="Process once and exit")
    args = ap.parse_args()

    if args.scan_dir:
        return run_scan_dir(args.scan_dir, once=args.once)

    print("No mode selected. Use --scan-dir for test mode. IMAP mode will be added later.")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

