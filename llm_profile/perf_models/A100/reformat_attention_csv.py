#!/usr/bin/env python3
"""Reformat attention CSV with separate prefill/decode stats columns.

The input CSV has only prefill-named stat columns (time_stats.attn_prefill.*).
Each row's is_prefill column (second-to-last) indicates whether the row is a
prefill or decode measurement. For decode rows, the stat values are currently
stored in the prefill columns — this script moves them to the correct decode
columns.

Usage:
  python reformat_attention_csv.py /path/to/attention.csv /path/to/attention.fixed.csv
"""

import argparse
import csv

PREFILL_STATS = [
    "time_stats.attn_prefill.min",
    "time_stats.attn_prefill.max",
    "time_stats.attn_prefill.mean",
    "time_stats.attn_prefill.median",
    "time_stats.attn_prefill.std",
]
DECODE_STATS = [
    "time_stats.attn_decode.min",
    "time_stats.attn_decode.max",
    "time_stats.attn_decode.mean",
    "time_stats.attn_decode.median",
    "time_stats.attn_decode.std",
]


def build_output_header(input_header):
    if all(c in input_header for c in DECODE_STATS):
        return list(input_header)
    other = [c for c in input_header if c not in PREFILL_STATS]
    return PREFILL_STATS + DECODE_STATS + other


def reformat_csv(in_path, out_path):
    with open(in_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        input_header = reader.fieldnames
        if input_header is None:
            raise ValueError("Input CSV has no header")

        if "is_prefill" not in input_header:
            raise ValueError("Input CSV has no is_prefill column")

        already_split = all(c in input_header for c in DECODE_STATS)
        output_header = build_output_header(input_header)

        with open(out_path, "w", newline="", encoding="utf-8") as out:
            writer = csv.DictWriter(out, fieldnames=output_header)
            writer.writeheader()

            prefill_count = decode_count = 0
            for row in reader:
                outrow = {c: "" for c in output_header}
                for c in input_header:
                    if c in outrow:
                        outrow[c] = row.get(c, "")

                if already_split:
                    writer.writerow(outrow)
                    continue

                is_prefill = row["is_prefill"].strip().lower() in ("1", "true", "t", "yes", "y")

                if is_prefill:
                    # Stats already in prefill columns; leave decode blank
                    for c in DECODE_STATS:
                        outrow[c] = ""
                    prefill_count += 1
                else:
                    # Stats are in prefill columns but belong in decode columns
                    for psrc, dsrc in zip(PREFILL_STATS, DECODE_STATS):
                        outrow[dsrc] = row.get(psrc, "")
                        outrow[psrc] = ""
                    decode_count += 1

                writer.writerow(outrow)

    print(f"Reformatted {in_path} -> {out_path}")
    print(f"  prefill rows: {prefill_count}, decode rows: {decode_count}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(
        description="Reformat attention CSV: split stats into prefill/decode columns using is_prefill flag"
    )
    ap.add_argument("input_csv", help="Input attention.csv file")
    ap.add_argument("output_csv", help="Output attention.csv file")
    args = ap.parse_args()

    reformat_csv(args.input_csv, args.output_csv)
