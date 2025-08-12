from __future__ import annotations
import argparse
import json
from pathlib import Path
from typing import List
from .extraction import run_extraction
from .schemas import CompanyInfo
from .tools import append_csv

def write_csv(items: List[CompanyInfo], out_csv: Path):
    out_csv.parent.mkdir(parents=True, exist_ok=True)
    # Start fresh file
    if out_csv.exists():
        out_csv.unlink()
    # Append each row through helper to ensure header + S.N. column
    for _i, item in enumerate(items, start=1):
        append_csv(
            csv_path=str(out_csv),
            company_name=item.company_name,
            founding_date=item.founding_date.isoformat(),
            founders=item.founders,
        )

def main():
    parser = argparse.ArgumentParser(description="Extract company info and export to CSV.")
    parser.add_argument("--input", type=str, default="data/essay.txt", help="Path to essay text file")
    parser.add_argument("--out", type=str, default="company_info.csv", help="Output CSV path")
    parser.add_argument("--preview", action="store_true", help="Print preview of extracted items")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of paragraphs for a quick run")
    args = parser.parse_args()

    text = Path(args.input).read_text(encoding="utf-8")
    items: List[CompanyInfo] = run_extraction(text, max_paragraphs=args.limit)

    # Optional preview
    if args.preview:
        for i, it in enumerate(items, 1):
            print(f"{i}. {it.company_name} | {it.founding_date.isoformat()} | {json.dumps(it.founders, ensure_ascii=False)}")

    write_csv(items, Path(args.out))
    print(f"Wrote {args.out} with {len(items)} rows.")

if __name__ == "__main__":
    main()