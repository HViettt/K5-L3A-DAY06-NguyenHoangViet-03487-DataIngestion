# Starter · PostgreSQL + pgvector (Giải pháp Lab đã hoàn thiện)

Dự án Data Ingestion Engineering cá nhân của học viên **Nguyễn Hoàng Việt (MSSV: 03487, Lớp L3A)**. Bộ code trong thư mục `src/` đã được hoàn thiện 100% để chạy ingestion pipeline, lưu trữ vector bền vững trên PostgreSQL + pgvector và thực thi benchmark đánh giá 3 chiến lược A, B, C.

## Cấu trúc thư mục

```text
starter/
├── docker-compose.yml        # PostgreSQL 16 + pgvector (127.0.0.1:55433)
├── init.sql                  # Script kích hoạt extension vector
├── requirements.txt          # psycopg, pgvector, pypdf, python-dotenv, google-genai
├── .env.example              # Cấu hình biến môi trường mẫu
├── scripts/
│   ├── check_setup.py        # Kiểm tra kết nối database và pgvector extension
│   └── create_benchmark.py   # Script kiểm tra và trích xuất 20 câu hỏi benchmark
└── src/
    ├── models.py             # Data class DocumentPage, Chunk
    ├── ingestion.py          # Trích xuất PDF và chuẩn hóa text (ngưỡng >= 300 ký tự)
    ├── chunking.py           # Chia chunk cố định (A: 500/50) và theo đoạn văn (B/C: max 800)
    ├── embeddings.py         # Google Gemini gemini-embedding-001 (768 dims) kèm local caching
    ├── store.py              # PostgreSQL + pgvector store, cosine search và metadata GIN index
    ├── evaluation.py         # Đánh giá Hit@1, Evidence Hit@3 và tổng hợp chỉ số
    └── run.py                # Pipeline điều phối toàn bộ quá trình nạp và đánh giá
```

## 1. Cài đặt và khởi động Database

Yêu cầu Docker Desktop hoặc Docker Engine và Python >= 3.10.

```bash
cd starter
# Cài đặt toàn bộ dependencies (bao gồm psycopg, pgvector, pypdf, google-genai, python-dotenv)
pip install -r requirements.txt

# Khởi động PostgreSQL + pgvector container
docker compose up -d --wait

# Kiểm tra kết nối database
python scripts/check_setup.py
```

Kỳ vọng: Hiện thông tin `Database: day6_lab | PostgreSQL: 16.x | pgvector: 0.8.7 | Setup OK`.
Container chạy tại `127.0.0.1:55433`, thông tin đăng nhập: `user: day6`, `pass: day6_local_only`, `db: day6_lab`.

## 2. Cấu hình biến môi trường

Tạo file `.env` từ mẫu:
```bash
cp .env.example .env
```

Điền `GEMINI_API_KEY`:
```env
DATABASE_URL=postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIM=768
```

## 3. Chạy Pipeline Ingestion & Benchmark

Bạn có thể chạy pipeline từ thư mục gốc của repository hoặc từ thư mục `starter/`:

```bash
# Cách 1 (Khuyến nghị): Chạy từ thư mục gốc repo
python -m starter.src.run
# hoặc
python starter/src/run.py

# Cách 2: Chạy từ trong thư mục starter/
cd starter
python -m src.run
# hoặc
python src/run.py
```

### Các bước pipeline thực thi tự động:
1. Đọc và chuẩn hóa 53 trang nội dung hợp lệ từ `data/so_tay_sinh_vien_2026.pdf` (loại bỏ 2 trang < 300 ký tự).
2. Tạo 279 chunks cho Strategy A (Fixed 500/50) và 184 chunks cho Strategy B & C (Paragraph max 800).
3. Tính embedding vector 768 chiều với `gemini-embedding-001` và nạp vào database pgvector có index.
4. Đánh giá truy xuất top-3 trên 20 câu hỏi benchmark (15 dev, 5 test).
5. Xuất traces chi tiết và tóm tắt kết quả ra thư mục `results/` cùng `artifacts/experiment_log.csv`.
