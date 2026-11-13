"""Implement fixed-size and structure-aware (paragraph) chunking."""
import re
from .models import Chunk, DocumentPage


def fixed_size(page: DocumentPage, size: int = 500, overlap: int = 50) -> list[Chunk]:
    """Split text into overlapping windows and retain page metadata (Strategy A)."""
    text = page.text
    if not text:
        return []
    
    chunks: list[Chunk] = []
    step = max(1, size - overlap)
    idx = 0
    start = 0
    
    while start < len(text):
        end = min(start + size, len(text))
        chunk_text = text[start:end].strip()
        
        if len(chunk_text) >= 40:  # Skip trivial micro-fragments
            chunk_id = f"{page.document_id}_p{page.page}_fix_{idx}"
            meta = dict(page.metadata)
            meta["chunk_type"] = "fixed_size"
            meta["start_char"] = start
            meta["end_char"] = end
            
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=chunk_text,
                    metadata=meta
                )
            )
            idx += 1
            
        if end >= len(text):
            break
        start += step
        
    return chunks


def by_paragraph(page: DocumentPage, max_size: int = 800) -> list[Chunk]:
    """Group paragraphs, split oversized paragraphs and retain metadata (Strategy B & C)."""
    text = page.text
    if not text:
        return []
    
    # Split text into logical paragraphs (using double newline or newline followed by indentation/heading)
    raw_paras = [p.strip() for p in re.split(r"\n{2,}|\n(?=[A-Z0-9\-\*\•IIVX\d]+\.|\bTC\d|\bĐiều\b|\bKhoản\b)", text) if p.strip()]
    if not raw_paras:
        raw_paras = [text]
        
    normalized_paras: list[str] = []
    for p in raw_paras:
        if len(p) <= max_size:
            normalized_paras.append(p)
        else:
            # Paragraph exceeds max_size: split by sentence
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", p) if s.strip()]
            cur_s = ""
            for s in sentences:
                if len(cur_s) + len(s) + 1 <= max_size:
                    cur_s = f"{cur_s} {s}".strip() if cur_s else s
                else:
                    if cur_s:
                        normalized_paras.append(cur_s)
                    cur_s = s
            if cur_s:
                normalized_paras.append(cur_s)
                
    # Group small paragraphs together to approach ~400-800 characters for optimal coherence
    chunks: list[Chunk] = []
    current_chunk = ""
    idx = 0
    
    for p in normalized_paras:
        if not current_chunk:
            current_chunk = p
        elif len(current_chunk) + len(p) + 2 <= max_size:
            current_chunk = f"{current_chunk}\n\n{p}"
        else:
            chunk_id = f"{page.document_id}_p{page.page}_para_{idx}"
            meta = dict(page.metadata)
            meta["chunk_type"] = "by_paragraph"
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    document_id=page.document_id,
                    source=page.source,
                    page=page.page,
                    text=current_chunk.strip(),
                    metadata=meta
                )
            )
            idx += 1
            current_chunk = p
            
    if current_chunk.strip():
        chunk_id = f"{page.document_id}_p{page.page}_para_{idx}"
        meta = dict(page.metadata)
        meta["chunk_type"] = "by_paragraph"
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=page.document_id,
                source=page.source,
                page=page.page,
                text=current_chunk.strip(),
                metadata=meta
            )
        )
        
    return chunks
