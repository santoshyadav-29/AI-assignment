from __future__ import annotations
from datetime import date
from typing import List, Union
from pydantic import BaseModel, field_validator
import re
from dateutil import parser as date_parser

MONTHS = {m.lower(): i for i, m in enumerate([
    "", "January","February","March","April","May","June","July","August","September","October","November","December"
])}

def normalize_partial_date(text: str) -> date:
    s = text.strip()
    # YYYY-MM-DD
    m_full = re.fullmatch(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m_full:
        y, mo, d = map(int, m_full.groups())
        return date(y, mo, d)

    # Month D, YYYY or D Month YYYY or Month YYYY
    try:
        # If day is missing, dateutil uses day=1; if month missing, we’ll handle below.
        dt = date_parser.parse(s, default=date(1900, 1, 1), dayfirst=False, fuzzy=True)
        # If only year present (e.g., "2010"), dateutil will set Jan 1 by default only if month absent.
        # We still need to detect if month was missing.
        year_match = re.fullmatch(r"\d{4}", s)
        if year_match:
            return date(int(year_match.group(0)), 1, 1)

        # Month YYYY (no day)
        month_year = re.fullmatch(r"([A-Za-z]+)\s+(\d{4})", s)
        if month_year:
            mo = MONTHS.get(month_year.group(1).lower(), 1)
            return date(int(month_year.group(2)), mo, 1)

        # Otherwise, trust the parsed full date
        return date(dt.year, dt.month, dt.day)
    except Exception:
        # Fallback: detect year; set defaults
        m_year = re.search(r"(\d{4})", s)
        if m_year:
            y = int(m_year.group(1))
            # Try detect month name
            m_name = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)", s, re.IGNORECASE)
            if m_name:
                mo = MONTHS[m_name.group(1).lower()]
                return date(y, mo, 1)
            return date(y, 1, 1)
        raise ValueError(f"Unrecognized date format: {text}")

class CompanyInfo(BaseModel):
    company_name: str
    founding_date: date
    founders: List[str]

    @field_validator("founding_date", mode="before")
    @classmethod
    def _parse_date(cls, v: Union[str, date]):
        if isinstance(v, date):
            return v
        return normalize_partial_date(str(v))

class ParagraphExtraction(BaseModel):
    items: List[CompanyInfo]