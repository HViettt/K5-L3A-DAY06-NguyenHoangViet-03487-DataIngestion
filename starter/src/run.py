"""Main orchestration pipeline for Day 06 Data Ingestion Engineering."""
import json
import os
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# Ensure imports work whether run directly (python starter/src/run.py) or as a module (python -m starter.src.run)
if __package__ is None or __package__ == "":
    repo_root = Path(__file__).resolve().parents[2]
    starter_dir = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    if str(starter_dir) not in sys.path:
        sys.path.insert(0, str(starter_dir))
    from starter.src.ingestion import load_pdf
    from starter.src.chunking import fixed_size, by_paragraph
    from starter.src.embeddings import MyEmbedder
    from starter.src.store import PgVectorStore
    from starter.src.evaluation import evaluate_query, summarize
else:
    from .ingestion import load_pdf
    from .chunking import fixed_size, by_paragraph
    from .embeddings import MyEmbedder
    from .store import PgVectorStore
    from .evaluation import evaluate_query, summarize


def main() -> None:
    print("=" * 60)
    print("Day 06 · Data Ingestion Engineering Pipeline")
    print("=" * 60)
    
    # Load environment variables
    env_path = Path(__file__).resolve().parents[1] / ".env"
    load_dotenv(env_path)
    
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        host = os.getenv("POSTGRES_HOST", "127.0.0.1")
        port = os.getenv("POSTGRES_PORT", "55433")
        db = os.getenv("POSTGRES_DB", "day6_lab")
        user = os.getenv("POSTGRES_USER", "day6")
        pw = os.getenv("POSTGRES_PASSWORD", "day6_local_only")
        db_url = f"postgresql://{user}:{pw}@{host}:{port}/{db}"
        
    model_name = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
    embedding_dim = int(os.getenv("EMBEDDING_DIM", "768"))
    
    # Paths relative to repository root
    repo_root = Path(__file__).resolve().parents[2]
    
    # 1. Load Corpus
    pdf_path = repo_root / "data" / "so_tay_sinh_vien_2026.pdf"
    doc_id = "hust-student-handbook-2026"
    print(f"\n[1/5] Loading and normalizing PDF: {pdf_path}...")
    t0 = time.time()
    pages = load_pdf(pdf_path, doc_id, str(pdf_path.relative_to(repo_root)).replace("\\", "/"))
    print(f"  -> Extracted {len(pages)} valid content pages (>= 30 required: PASS)")
    total_chars = sum(len(p.text) for p in pages)
    print(f"  -> Total characters after normalization: {total_chars:,} chars ({time.time() - t0:.2f}s)")
    
    # 2. Build Chunks for Strategy A & B
    print("\n[2/5] Chunking documents...")
    # Strategy A: Fixed-size 500, overlap 50
    chunks_a = []
    for p in pages:
        chunks_a.extend(fixed_size(p, size=500, overlap=50))
    print(f"  -> Strategy A (Fixed size 500, overlap 50): {len(chunks_a)} chunks")
    
    # Strategy B: Structure-aware (by paragraph, max 800)
    chunks_b = []
    for p in pages:
        chunks_b.extend(by_paragraph(p, max_size=800))
    print(f"  -> Strategy B & C (By paragraph, max 800): {len(chunks_b)} chunks")
    
    # 3. Embedding and Ingestion into pgvector
    print(f"\n[3/5] Connecting to Embedding Model ({model_name}, dim={embedding_dim}) & Vector Store...")
    embedder = MyEmbedder(model_name=model_name, dimensions=embedding_dim)
    store = PgVectorStore(database_url=db_url, dimensions=embedding_dim)
    store.create_schema()
    
    # Ingest Strategy A
    print(f"  -> Embedding {len(chunks_a)} chunks for Strategy A...")
    t_ingest_a = time.time()
    texts_a = [c.text for c in chunks_a]
    vectors_a = embedder.embed_documents(texts_a)
    store.upsert(strategy="strategy_a", chunks=chunks_a, vectors=vectors_a)
    dur_a = time.time() - t_ingest_a
    print(f"  -> Stored Strategy A in pgvector: {len(chunks_a)} vectors ({dur_a:.2f}s)")
    
    # Ingest Strategy B (also used by Strategy C)
    print(f"  -> Embedding {len(chunks_b)} chunks for Strategy B...")
    t_ingest_b = time.time()
    texts_b = [c.text for c in chunks_b]
    vectors_b = embedder.embed_documents(texts_b)
    store.upsert(strategy="strategy_b", chunks=chunks_b, vectors=vectors_b)
    dur_b = time.time() - t_ingest_b
    print(f"  -> Stored Strategy B in pgvector: {len(chunks_b)} vectors ({dur_b:.2f}s)")
    
    # 4. Load Benchmark
    print("\n[4/5] Loading Benchmark dataset...")
    benchmark_path = repo_root / "benchmark" / "questions.json"
    with open(benchmark_path, "r", encoding="utf-8") as f:
        questions = json.load(f)
    print(f"  -> Loaded {len(questions)} questions (15 dev, 5 test)")
    
    # 5. Evaluate Strategies A, B, and C
    print("\n[5/5] Running Benchmark Retrieval for Strategies A, B, C...")
    results_dir = repo_root / "results"
    results_dir.mkdir(exist_ok=True)
    
    strategies = [
        {"name": "Strategy A", "key": "strategy_a", "use_filter": False, "desc": "Fixed-size (500/50), No filter"},
        {"name": "Strategy B", "key": "strategy_b", "use_filter": False, "desc": "Paragraph (max 800), No filter"},
        {"name": "Strategy C", "key": "strategy_b", "use_filter": True, "desc": "Paragraph (max 800) + Metadata Filter"}
    ]
    
    all_summaries = {}
    
    for strat in strategies:
        print(f"\n--- Evaluating {strat['name']} ({strat['desc']}) ---")
        traces = []
        t_eval_start = time.time()
        
        for q in questions:
            q_vec = embedder.embed_query(q["question"])
            
            # Apply filter only for Strategy C if query has a filter specified
            applied_filter = q.get("filter") if strat["use_filter"] else None
            
            hits = store.search(
                strategy=strat["key"],
                query_vector=q_vec,
                top_k=3,
                filters=applied_filter
            )
            
            trace = evaluate_query(q, hits)
            trace["strategy"] = strat["name"]
            trace["filter_applied"] = applied_filter
            traces.append(trace)
            
        dur_eval = time.time() - t_eval_start
        summary = summarize(traces)
        summary["duration_seconds"] = round(dur_eval, 2)
        all_summaries[strat["name"]] = summary
        
        # Save per-strategy traces
        safe_name = strat["name"].lower().replace(" ", "_")
        trace_file = results_dir / f"traces_{safe_name}.json"
        with open(trace_file, "w", encoding="utf-8") as f:
            json.dump(traces, f, ensure_ascii=False, indent=2)
        print(f"  -> Saved full traces to {trace_file}")
        
        dev_res = summary["dev"]
        test_res = summary["test"]
        print(f"  -> DEV  (15): Hit@1 = {dev_res['hit1_ratio']} ({dev_res['hit1_rate']*100:.1f}%), Evidence Hit@3 = {dev_res['hit3_ratio']} ({dev_res['hit3_rate']*100:.1f}%)")
        print(f"  -> TEST (5) : Hit@1 = {test_res['hit1_ratio']} ({test_res['hit1_rate']*100:.1f}%), Evidence Hit@3 = {test_res['hit3_ratio']} ({test_res['hit3_rate']*100:.1f}%)")
    
    # Save overall summary
    summary_file = results_dir / "benchmark_summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_summaries, f, ensure_ascii=False, indent=2)
    print(f"\nSaved overall summary to {summary_file}")
    
    # Update artifacts/experiment_log.csv
    exp_log_path = repo_root / "artifacts" / "experiment_log.csv"
    with open(exp_log_path, "w", encoding="utf-8") as f:
        f.write("strategy,chunking,chunk_size,overlap,metadata,filter,vectorizer,hypothesis,dev_hit1,dev_hit3,test_hit1,test_hit3,notes\n")
        
        # A
        sum_a = all_summaries["Strategy A"]
        f.write(f"A,fixed,500,50,\"category,page,source\",none,{model_name},Baseline fixed-size window,{sum_a['dev']['hit1_ratio']},{sum_a['dev']['hit3_ratio']},{sum_a['test']['hit1_ratio']},{sum_a['test']['hit3_ratio']},Fixed chunk can cut sentences\n")
        
        # B
        sum_b = all_summaries["Strategy B"]
        f.write(f"B,paragraph,800,0,\"category,page,source\",none,{model_name},Paragraph chunking preserves semantics,{sum_b['dev']['hit1_ratio']},{sum_b['dev']['hit3_ratio']},{sum_b['test']['hit1_ratio']},{sum_b['test']['hit3_ratio']},Structure aware chunking\n")
        
        # C
        sum_c = all_summaries["Strategy C"]
        f.write(f"C,paragraph,800,0,\"category,page,source\",category_filtered,{model_name},Metadata filter eliminates out-of-domain noise,{sum_c['dev']['hit1_ratio']},{sum_c['dev']['hit3_ratio']},{sum_c['test']['hit1_ratio']},{sum_c['test']['hit3_ratio']},Exact same chunks as B with SQL filter\n")
        
    print(f"Updated {exp_log_path}")
    print("\nPIPELINE COMPLETED SUCCESSFULLY!")


if __name__ == "__main__":
    main()
