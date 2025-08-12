from __future__ import annotations
import os
import re
from typing import List
import time
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from .schemas import ParagraphExtraction, CompanyInfo

def build_llm(model_name: str = None, temperature: float = 0.0):
    # Ensure .env is loaded so GEMINI_API_KEY is available
    load_dotenv()
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY or GEMINI_API_KEY is not set")
    api_key = api_key.strip()
    model = model_name or os.getenv("GENAI_MODEL", "gemini-1.5-flash")
    return ChatGoogleGenerativeAI(model=model, temperature=temperature, api_key=api_key)

def split_into_paragraphs(text: str) -> List[str]:
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    return paras

def _build_one_paragraph_chain():
    llm = build_llm()
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "Extract company founding facts from the paragraph. "
         "Return items as a JSON object matching the schema 'ParagraphExtraction'. "
         "Each item must include: company_name (string), founding_date (string, can be YYYY, YYYY-MM or YYYY-MM-DD), "
         "and founders (list of strings; only real human names). "
         "If multiple companies are present, include them all."),
        ("human", "{paragraph}")
    ])
    structured = llm.with_structured_output(ParagraphExtraction)
    return prompt | structured

def run_extraction(text: str, delay_sec: float = 1.0, max_paragraphs: int | None = None) -> List[CompanyInfo]:
    """Sequentially process each paragraph to avoid rate limits and return flat items."""
    paragraphs = split_into_paragraphs(text)
    if max_paragraphs:
        paragraphs = paragraphs[:max_paragraphs]
    one = _build_one_paragraph_chain()
    results: List[ParagraphExtraction] = []
    for i, p in enumerate(paragraphs, 1):
        r: ParagraphExtraction = one.invoke({"paragraph": p})
        results.append(r)
        if delay_sec:
            time.sleep(delay_sec)
    items: List[CompanyInfo] = []
    for r in results:
        items.extend(r.items)
    return items