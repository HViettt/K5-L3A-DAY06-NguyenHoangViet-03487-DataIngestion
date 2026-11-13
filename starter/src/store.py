"""Store and search vectors using PostgreSQL + pgvector."""
import json
from typing import Any
import psycopg
from .models import Chunk


class PgVectorStore:
    def __init__(self, database_url: str, dimensions: int = 768) -> None:
        self.database_url = database_url
        self.dimensions = dimensions

    def create_schema(self) -> None:
        """Create extension and table with vector column and metadata."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                cur.execute(f"""
                    CREATE TABLE IF NOT EXISTS chunks (
                        strategy VARCHAR(32) NOT NULL,
                        chunk_id VARCHAR(128) NOT NULL,
                        document_id VARCHAR(128) NOT NULL,
                        source VARCHAR(256) NOT NULL,
                        page INTEGER NOT NULL,
                        text TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({self.dimensions}) NOT NULL,
                        PRIMARY KEY (strategy, chunk_id)
                    );
                    CREATE INDEX IF NOT EXISTS idx_chunks_strategy ON chunks(strategy);
                    CREATE INDEX IF NOT EXISTS idx_chunks_metadata ON chunks USING gin(metadata);
                """)
            conn.commit()

    def upsert(self, strategy: str, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        """Validate lengths/dimensions and write stable IDs without duplicates.
        
        Removes obsolete chunks for the strategy to guarantee idempotent re-ingestion.
        """
        if len(chunks) != len(vectors):
            raise ValueError(f"Mismatch: {len(chunks)} chunks vs {len(vectors)} vectors")
        
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                # Remove obsolete records for this strategy first
                cur.execute("DELETE FROM chunks WHERE strategy = %s", (strategy,))
                
                # Bulk insert new chunks
                insert_query = """
                    INSERT INTO chunks (strategy, chunk_id, document_id, source, page, text, metadata, embedding)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector)
                    ON CONFLICT (strategy, chunk_id) DO UPDATE SET
                        text = EXCLUDED.text,
                        metadata = EXCLUDED.metadata,
                        embedding = EXCLUDED.embedding;
                """
                records = [
                    (
                        strategy,
                        c.chunk_id,
                        c.document_id,
                        c.source,
                        c.page,
                        c.text,
                        json.dumps(c.metadata, ensure_ascii=False),
                        str(v)
                    )
                    for c, v in zip(chunks, vectors)
                ]
                cur.executemany(insert_query, records)
            conn.commit()

    def search(self, strategy: str, query_vector: list[float], top_k: int = 3,
               filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Filter metadata in SQL, rank by cosine distance (<=>), return top-k."""
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                if filters and len(filters) > 0:
                    query = """
                        SELECT chunk_id, document_id, source, page, text, metadata,
                               (embedding <=> %s::vector) AS distance
                        FROM chunks
                        WHERE strategy = %s AND metadata @> %s::jsonb
                        ORDER BY distance ASC
                        LIMIT %s;
                    """
                    cur.execute(query, (str(query_vector), strategy, json.dumps(filters), top_k))
                else:
                    query = """
                        SELECT chunk_id, document_id, source, page, text, metadata,
                               (embedding <=> %s::vector) AS distance
                        FROM chunks
                        WHERE strategy = %s
                        ORDER BY distance ASC
                        LIMIT %s;
                    """
                    cur.execute(query, (str(query_vector), strategy, top_k))
                
                rows = cur.fetchall()
                results = []
                for row in rows:
                    dist = float(row[6])
                    score = round(1.0 - dist, 4)  # Cosine similarity score
                    results.append({
                        "chunk_id": row[0],
                        "document_id": row[1],
                        "source": row[2],
                        "page": int(row[3]),
                        "text": row[4],
                        "metadata": row[5],
                        "distance": dist,
                        "score": score
                    })
                return results
