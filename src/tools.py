from __future__ import annotations
import csv
import json
import sqlite3
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from .schemas import CompanyInfo

class CSVArgs(BaseModel):
    csv_path: str = Field(..., description="Path to CSV file to append")
    company_name: str
    founding_date: str  # YYYY-MM-DD
    founders: List[str]

def append_csv(csv_path: str, company_name: str, founding_date: str, founders: List[str]) -> str:
    path = Path(csv_path)
    new_file = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if new_file:
            writer.writerow(["S.N.", "Company Name", "Founded in", "Founded by"])
        # Compute S.N. by counting lines (expensive for very large files; ok for assignment)
        sn = 1
        if path.exists():
            try:
                with path.open("r", encoding="utf-8") as r:
                    sn = sum(1 for _ in r)  # includes header
                sn = max(1, sn - 0)  # we’ll correct below
            except Exception:
                sn = 1
        # Recount rows properly if needed
        try:
            with path.open("r", encoding="utf-8") as r:
                rows = list(csv.reader(r))
            sn = len(rows)  # header is row 1
        except Exception:
            sn = 1
        founders_str = json.dumps(founders, ensure_ascii=False)
        writer.writerow([sn, company_name, founding_date, founders_str])
    return f"Appended to {csv_path}"

append_csv_tool = StructuredTool.from_function(
    func=append_csv,
    name="append_company_to_csv",
    description="Append one company row into a CSV file with columns [S.N., Company Name, Founded in, Founded by].",
    args_schema=CSVArgs,
)

# Optional: SQLite upsert tool
class SQLArgs(BaseModel):
    db_path: str = Field(..., description="Path to SQLite database")
    company_name: str
    founding_date: str
    founders: List[str]

def upsert_sqlite(db_path: str, company_name: str, founding_date: str, founders: List[str]) -> str:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS companies (
              company_name TEXT PRIMARY KEY,
              founding_date TEXT,
              founders TEXT
            )
        """)
        founders_json = json.dumps(founders, ensure_ascii=False)
        cur.execute("""
            INSERT INTO companies (company_name, founding_date, founders)
            VALUES (?, ?, ?)
            ON CONFLICT(company_name) DO UPDATE SET
              founding_date=excluded.founding_date,
              founders=excluded.founders
        """, (company_name, founding_date, founders_json))
        conn.commit()
        return f"Upserted {company_name}"
    finally:
        conn.close()

upsert_sqlite_tool = StructuredTool.from_function(
    func=upsert_sqlite,
    name="upsert_company_sqlite",
    description="Upsert a company row into a SQLite DB (table: companies).",
    args_schema=SQLArgs,
)