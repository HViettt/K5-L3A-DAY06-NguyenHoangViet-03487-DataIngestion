# Day 06 · Data Ingestion Engineering

**Học viên:** Nguyễn Hoàng Việt (MSSV: `03487`, Lớp: `L3A`) · **Corpus:** Sổ tay Sinh viên Đại học Bách khoa Hà Nội 2026

Dự án hiện thực trọn vẹn pipeline Data Ingestion Engineering phục vụ hệ thống RAG: trích xuất, chuẩn hóa, phân tích chiến lược chia chunk, vector hóa bằng Google Gemini Embedding API, lưu trữ trên PostgreSQL/pgvector và đánh giá hiệu năng truy xuất trên bộ benchmark kiểm thử đa khía cạnh.

| 📄 Dữ liệu | 🧩 Chiến lược | 🎯 Benchmark |
|---|---|---|
| **53 trang nội dung hợp lệ** ($\ge 300$ ký tự) | **3 cấu hình so sánh** (A, B, C; C dùng lại chunks của B và thêm metadata filter) | **20 câu hỏi** (15 dev / 5 test) |

## Bắt đầu nhanh

Hệ thống đã được hiện thực hoàn chỉnh và sẵn sàng chạy tái hiện:
1. Khởi động vector store: `cd starter && docker compose up -d`
2. Cài đặt thư viện: `pip install -r starter/requirements.txt`
3. Cấu hình khóa `GEMINI_API_KEY` trong `starter/.env`
4. Chạy toàn bộ pipeline & benchmark: `python -m starter.src.run`

## 1. Kiến trúc Pipeline

![Đọc tài liệu, chuẩn hóa, chia chunk, tạo vector, lưu và kiểm tra](assets/ingestion-pipeline.svg)

- **Corpus & Tiền xử lý:** Trích xuất 53 trang nội dung hợp lệ từ Sổ tay Sinh viên HUST 2026 (115.455 ký tự chuẩn hóa), tự động lọc bỏ các trang bìa/mục lục dưới 300 ký tự, chuẩn hóa Unicode NFKC, xử lý ngắt từ và bảo toàn ranh giới đoạn.
- **Embedding & Storage:** Tích hợp mô hình `gemini-embedding-001` (768 chiều) với cơ chế disk cache thông minh và lưu trữ trong bảng `chunks` của PostgreSQL 16 + pgvector (`vector_cosine_ops`).

## 2. Chiến lược Chunking & Benchmark

![Ba chiến lược được đánh giá trên cùng corpus và benchmark dev/test](assets/benchmark-workflow.svg)

Hệ thống triển khai và so sánh đối chứng 3 chiến lược:
- **Strategy A (Baseline):** Fixed-size window (`chunk_size = 500`, `overlap = 50`), không lọc metadata (sinh ra 279 chunks).
- **Strategy B (Structure-aware):** Paragraph chunking theo ranh giới đoạn văn tự nhiên `\n\n` (`max_size = 800`), không lọc metadata (sinh ra 184 chunks).
- **Strategy C (Paragraph + Filter):** Sử dụng chính xác 184 chunks và vectors của Strategy B, kích hoạt bộ lọc JSONB metadata trong PostgreSQL (`@> '{"category": ...}'::jsonb`) cho các câu hỏi chuyên biệt.

Bộ benchmark gồm **20 câu hỏi** (15 câu dev / 5 câu test cố định) đánh giá qua 5 tiêu chí: **Độ chính xác truy xuất (Hit@1, Evidence Hit@3)**, **Tính mạch lạc (Coherence)**, **Tính hữu dụng của Metadata (Metadata Audit & Domain Isolation)**, **Chất lượng Grounding** và **Tác động của chiến lược dữ liệu**.

## 3. Cấu trúc bài nộp

- Toàn bộ traces top-3, kết quả benchmark tổng hợp và nhật ký audit thủ công được lưu tại [results/](results/).
- Thông tin học viên tại [STUDENT.md](STUDENT.md) và nhật ký thí nghiệm tại [artifacts/experiment_log.csv](artifacts/experiment_log.csv).
- Báo cáo phân tích chuyên sâu tại [report/individual/03487_NguyenHoangViet.md](report/individual/03487_NguyenHoangViet.md).

## Tài liệu tham khảo của lab

| Tài liệu | Mô tả |
|---|---|
| [starter/README.md](starter/README.md) | Chi tiết triển khai mã nguồn và database pgvector |
| [GUIDE.md](GUIDE.md) | Các bước làm và cách tính chỉ số |
| [CHECKPOINTS.md](CHECKPOINTS.md) | Tiến độ trong 4 giờ |
| [BENCHMARK.md](BENCHMARK.md) | Năm tiêu chí benchmark và bộ câu hỏi |
| [RUBRIC.md](RUBRIC.md) | Tiêu chí chấm điểm |
| [RULES.md](RULES.md) | Quy tắc sử dụng dữ liệu, AI và API |
| [SUBMISSION.md](SUBMISSION.md) | Checklist nộp bài |

---

## Hướng dẫn tái hiện thí nghiệm (Reproduction Guide)

### 1. Thông tin sinh viên & Báo cáo
- **Học viên:** Nguyễn Hoàng Việt (MSSV: `03487`, Lớp: `L3A`)
- **Corpus:** Tải PDF asset từ GitHub Release `day6-submission` và lưu thành `data/so_tay_sinh_vien_2026.pdf` trước khi chạy pipeline (55 trang vật lý; 53 trang nội dung hợp lệ; 115.455 ký tự chuẩn hóa).
- **Manifest:** [data/manifest.json](data/manifest.json)
- **Benchmark:** [benchmark/questions.json](benchmark/questions.json) (20 câu: 15 dev / 5 test)
- **Báo cáo cá nhân chi tiết:** [report/individual/03487_NguyenHoangViet.md](report/individual/03487_NguyenHoangViet.md)
- **Traces & Kết quả:** [results/](results/)

### 2. Yêu cầu môi trường & Cài đặt

#### a. Khởi động PostgreSQL + pgvector
```bash
cd starter
docker compose up -d
```
Database chạy tại `localhost:55433` (user: `day6`, pass: `day6_local_only`, db: `day6_lab`).

#### b. Cài đặt thư viện Python
```bash
pip install -r starter/requirements.txt
```
*(Yêu cầu Python >= 3.10, bao gồm `psycopg[binary]`, `pgvector`, `pypdf`, `google-genai`, `python-dotenv`).*

#### c. Thiết lập biến môi trường
Tạo file `starter/.env` từ mẫu:
```bash
cp starter/.env.example starter/.env
```
Cấu hình trong `starter/.env`:
```env
# Chuỗi kết nối PostgreSQL chuẩn (khớp với docker-compose.yml)
DATABASE_URL=postgresql://day6:day6_local_only@127.0.0.1:55433/day6_lab

# Khóa API và mô hình embedding
GEMINI_API_KEY=your_gemini_api_key_here
EMBEDDING_MODEL=gemini-embedding-001
EMBEDDING_DIM=768
```
*(Hệ thống cũng hỗ trợ tự ghép nối từ các biến riêng lẻ `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD` nếu `DATABASE_URL` không được cung cấp).*

#### d. Kiểm tra kết nối
```bash
python starter/scripts/check_setup.py
```

### 3. Chạy pipeline Ingestion & Benchmark

Chạy toàn bộ pipeline từ thư mục gốc của repository (thực hiện nạp dữ liệu, chunking cho 3 chiến lược, tính embedding, lưu vào Postgres và chạy đánh giá trên 20 câu benchmark):

```bash
# Cách 1 (Khuyến nghị): Chạy dưới dạng module
python -m starter.src.run

# Cách 2: Chạy trực tiếp script
python starter/src/run.py
```

### 4. Kết quả đầu ra
- `results/traces_strategy_a.json`: Trace top-3 retrieval cho Strategy A (Fixed-size 500/50).
- `results/traces_strategy_b.json`: Trace top-3 retrieval cho Strategy B (Paragraph chunking max 800).
- `results/traces_strategy_c.json`: Trace top-3 retrieval cho Strategy C (Paragraph + SQL metadata filter).
- `results/benchmark_summary.json`: Bảng tổng hợp Hit@1, Hit@3 trên tập Dev và Test.
- `results/manual_audit.json`: Nhật ký chấm điểm thủ công 5 khía cạnh (Coherence, Grounding, Metadata).
- `artifacts/experiment_log.csv`: Nhật ký các lần chạy thử nghiệm.

