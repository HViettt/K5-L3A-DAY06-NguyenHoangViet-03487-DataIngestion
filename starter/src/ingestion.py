"""Read and normalize source data."""
import logging
import warnings
import unicodedata
import re
from pathlib import Path

# Suppress benign pypdf Type1 font warnings (fontTools optional)
warnings.filterwarnings("ignore")
logging.getLogger("pypdf").setLevel(logging.ERROR)

import pypdf

from .models import DocumentPage


def get_page_category(page_num: int) -> str:
    """Classify handbook pages into reliable categories defined in manifest.json."""
    if page_num in [2, 3] or page_num >= 24:
        return "gioi_thieu_vien_khoa"
    elif page_num in [10, 11, 14, 15, 16]:
        return "diem_ren_luyen"
    elif page_num in [17, 21, 22]:
        return "hoc_bong_an_sinh"
    else:
        return "quy_che_quy_dinh"


def normalize_text(text: str) -> str:
    """Normalize Unicode and whitespace without discarding useful paragraph structure."""
    if not text:
        return ""
    
    # 1. Normalize Unicode to NFKC
    norm = unicodedata.normalize("NFKC", text)
    
    # 2. Normalize non-breaking spaces and special whitespace
    norm = norm.replace("\u00a0", " ").replace("\ufeff", "")
    
    # 3. Standardize newlines
    norm = norm.replace("\r\n", "\n").replace("\r", "\n")
    
    # 4. Remove hyphenation at line breaks (e.g., 'ĐHB -\nKHN' -> 'ĐHBK HN' or 'từ-\nđiển')
    norm = re.sub(r"(\w+)\s*-\s*\n\s*(\w+)", r"\1\2", norm)
    
    # 5. Clean excessive spaces within lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in norm.split("\n")]
    
    # 6. Recombine paragraphs: keep double newlines for paragraph boundaries
    cleaned_text = "\n".join(lines)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)
    
    return cleaned_text.strip()


def load_pdf(path: Path, document_id: str, source: str) -> list[DocumentPage]:
    """Extract each physical page; keep its page number, category, and source.
    
    Detect and record pages with no text or excluded pages (e.g. cover, TOC).
    """
    if not path.exists():
        raise FileNotFoundError(f"Corpus file not found: {path}")
    
    reader = pypdf.PdfReader(str(path))
    pages: list[DocumentPage] = []
    
    # Rule: Only include content pages with at least 300 characters after normalization
    # Pages with < 300 chars (Page 1 cover with 35 chars, Page 4 TOC with 292 chars) are automatically excluded
    MIN_PAGE_CHAR_THRESHOLD = 300
    
    for idx, pdf_page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = pdf_page.extract_text() or ""
        text = normalize_text(raw_text)
        
        if len(text) < MIN_PAGE_CHAR_THRESHOLD:
            # Exclude blank or near-blank pages (< 300 characters)
            continue
        
        category = get_page_category(page_num)
        
        doc_page = DocumentPage(
            document_id=document_id,
            source=source,
            page=page_num,
            text=text,
            metadata={
                "category": category,
                "char_count": len(text),
                "physical_page": page_num
            }
        )
        pages.append(doc_page)
        
    return pages
