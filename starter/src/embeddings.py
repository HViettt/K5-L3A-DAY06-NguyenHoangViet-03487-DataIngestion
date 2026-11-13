"""Real embedding provider adapter using Google Gemini API with local disk caching."""
import json
import os
import time
from pathlib import Path
from typing import Protocol
from dotenv import load_dotenv
from google import genai
from google.genai import types


class Embedder(Protocol):
    model_name: str
    dimensions: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in the same order."""
        ...

    def embed_query(self, question: str) -> list[float]:
        """Return a query vector compatible with the stored document vectors."""
        ...


class MyEmbedder:
    """Real embedder adapter using Gemini embedding model with caching to conserve quota."""

    def __init__(self, model_name: str = "gemini-embedding-001", dimensions: int = 768) -> None:
        starter_dir = Path(__file__).resolve().parents[1]
        load_dotenv(starter_dir / ".env")
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY missing from environment or .env file.")
        
        self.model_name = model_name
        self.dimensions = dimensions
        self.client = genai.Client(api_key=api_key)
        self.config = types.EmbedContentConfig(output_dimensionality=self.dimensions)
        
        # Local file-based cache to avoid redundant API requests & conserve free-tier quota
        self.cache_file = starter_dir / ".cache_embeddings.json"
        self._cache: dict[str, list[float]] = {}
        self._load_cache()

    def _load_cache(self) -> None:
        if self.cache_file.exists():
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    self._cache = json.load(f)
            except Exception:
                self._cache = {}

    def _save_cache(self) -> None:
        try:
            with open(self.cache_file, "w", encoding="utf-8") as f:
                json.dump(self._cache, f, ensure_ascii=False)
        except Exception:
            pass

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Batch embed multiple texts reliably with cache and rate-limiting handling."""
        if not texts:
            return []
        
        results: list[list[float] | None] = [None] * len(texts)
        missing_indices: list[int] = []
        missing_texts: list[str] = []
        
        for idx, t in enumerate(texts):
            if t in self._cache:
                results[idx] = self._cache[t]
            else:
                missing_indices.append(idx)
                missing_texts.append(t)
                
        if not missing_texts:
            return [r for r in results if r is not None]
        
        print(f"    (Embedding {len(missing_texts)} new texts via Gemini API, {len(texts) - len(missing_texts)} cached)...")
        
        # Gemini free tier supports up to 80-100 items per batch
        batch_size = 40
        
        for b_start in range(0, len(missing_texts), batch_size):
            b_end = min(b_start + batch_size, len(missing_texts))
            batch = missing_texts[b_start:b_end]
            indices = missing_indices[b_start:b_end]
            
            for attempt in range(8):
                try:
                    res = self.client.models.embed_content(
                        model=self.model_name,
                        contents=batch,
                        config=self.config
                    )
                    batch_vectors = [emb.values for emb in res.embeddings]
                    
                    for orig_idx, text_item, vec in zip(indices, batch, batch_vectors):
                        results[orig_idx] = vec
                        self._cache[text_item] = vec
                    
                    self._save_cache()
                    break
                except Exception as e:
                    err_msg = str(e)
                    wait_sec = 25
                    if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                        print(f"    [Rate limit 429] Waiting {wait_sec}s before retry (attempt {attempt+1}/8)...")
                        time.sleep(wait_sec)
                    else:
                        print(f"    [Error] {err_msg[:100]}... Retrying in 5s...")
                        time.sleep(5)
                    if attempt == 7:
                        raise RuntimeError(f"Embedding failed after 8 attempts: {e}")
                        
            time.sleep(1.0)
            
        return [r for r in results if r is not None]

    def embed_query(self, question: str) -> list[float]:
        """Embed a single query with cache support."""
        if question in self._cache:
            return self._cache[question]
            
        for attempt in range(6):
            try:
                res = self.client.models.embed_content(
                    model=self.model_name,
                    contents=question,
                    config=self.config
                )
                vec = res.embeddings[0].values
                self._cache[question] = vec
                self._save_cache()
                return vec
            except Exception as e:
                err_msg = str(e)
                wait_sec = 15
                if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                    print(f"    [Rate limit 429 on query] Waiting {wait_sec}s...")
                    time.sleep(wait_sec)
                else:
                    time.sleep(3)
                if attempt == 5:
                    raise RuntimeError(f"Embedding query failed: {e}")
                    
        raise RuntimeError("embed_query failed")
