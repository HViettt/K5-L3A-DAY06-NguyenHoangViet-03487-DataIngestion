# Báo cáo cá nhân — Day 6: Data Ingestion Engineering

- **Họ và tên:** Nguyễn Hoàng Việt
- **MSSV:** 03487
- **Lớp:** L3A
- **Repository:** `K5-L3A-DAY06-NguyenHoangViet-03487-DataIngestion`

---

## Dữ liệu và pipeline

- **Chủ đề, nguồn/quyền, số trang và quy tắc tính trang:**
  - *Chủ đề:* Sổ tay Sinh viên 2026 (Cẩm nang hướng dẫn sinh viên, Đại học Bách khoa Hà Nội).
  - *Source and usage scope:* HUST Student Affairs portal (`https://ctt.hust.edu.vn/DisplayWeb/DisplayBaiViet.aspx?baiviet=42750`). The handbook is publicly posted for reference. The source page reviewed does not state a redistribution license; use in this academic lab is documented, while permission to redistribute the full PDF has not been confirmed.
  - *Kế toán số trang:* Tổng cộng 55 trang vật lý. Loại trừ 2 trang: Trang 1 (bìa trước: 35 ký tự thô / 35 ký tự chuẩn hóa) và Trang 4 (mục lục tóm tắt: 293 ký tự thô / 292 ký tự chuẩn hóa) do dưới ngưỡng 300 ký tự.
  - *Quy tắc tính trang:* Tính tất cả các trang có nội dung quy định, điều khoản, hướng dẫn học vụ, quy chế rèn luyện hoặc thông tin giới thiệu đào tạo thực tế có $\ge 300$ ký tự sau chuẩn hóa. Số trang nội dung hợp lệ được tính là **53 trang** (tất cả 53 trang hợp lệ đều đạt từ 615 đến 7.545 ký tự chuẩn hóa, vượt xa mốc tối thiểu $\ge 30$ trang theo quy định). Quy tắc này được code hóa trực tiếp trong `starter/src/ingestion.py` (`len(text) < 300`).
  - *Tổng số ký tự văn bản:* Toàn bộ file PDF gồm 117.465 ký tự thô; tổng số ký tự chuẩn hóa đưa vào chia chunking là **115.455 ký tự**.

- **Chuẩn hóa, lỗi và giới hạn:**
  - *Chuẩn hóa:* Áp dụng chuẩn Unicode NFKC (`unicodedata.normalize`), loại bỏ non-breaking space `\u00a0`, chuẩn hóa các ký tự xuống dòng `\r\n` thành `\n`, khử nối từ do ngắt dòng (hyphenation ghép từ như `ĐHB -\nKHN` thành `ĐHBKHN`), loại bỏ khoảng trắng thừa nhưng bảo tồn nguyên vẹn dấu ngắt đoạn `\n\n`.
  - *Lỗi & giới hạn trích xuất:* Một số bảng biểu có định dạng font Type1 đặc biệt phát sinh cảnh báo fontTools nhưng vẫn trích xuất được 100% text tiếng Việt có dấu. Bảng tính điểm rèn luyện dạng cột khi trích xuất text thô chuyển thành dòng tuần tự nên cần gom nhóm đoạn hợp lý để không mất ngữ cảnh tiêu chí.

- **Embedding model, Vector store, Metric, Lệnh chạy và Chi phí:**
  - *Embedding model:* Google Gemini `gemini-embedding-001`, trích xuất vector thực 768 chiều (`output_dimensionality=768`).
  - *Vector store:* PostgreSQL 16 kết hợp extension `pgvector 0.8.7` chạy Docker Compose local (cổng `127.0.0.1:55433`).
  - *Metric tìm kiếm:* Cosine distance (toán tử `<=>` của pgvector), chuyển đổi sang Cosine similarity score = $1.0 - \text{distance}$.
  - *Lệnh chạy pipeline:* Hỗ trợ chạy dạng module `python -m starter.src.run` hoặc chạy trực tiếp script `python starter/src/run.py`.
  - *Chi phí:* \$0 (Sử dụng hạn ngạch Google AI Studio Free Tier kết hợp cơ chế cache đĩa cục bộ `starter/.cache_embeddings.json`).
  - *Phân rã thời gian chạy:* Tổng thời gian thực thi pipeline đo được gồm: trích xuất & chuẩn hóa PDF (~18.8 giây), sinh chunking (< 0.05 giây), tính embedding & nạp pgvector (141.86s khi nạp mới chưa cache / 0.24s khi có cache đĩa), và đánh giá truy xuất 20 câu benchmark (~10 giây).

- **Metadata bắt buộc, trường lọc bổ sung, nguồn giá trị và lý do chọn:**
  - *Metadata bắt buộc:* `document_id` (`hust-student-handbook-2026`), `source` (`data/so_tay_sinh_vien_2026.pdf`), `page` (số trang vật lý PDF để truy vết nguồn gốc bằng chứng).
  - *Trường lọc bổ sung (`category`):* Phân loại thành 4 nhóm giá trị đáng tin cậy dựa trên cấu trúc các chương mục của sổ tay:
    1. `quy_che_quy_dinh`: Nội quy, quy định chung, gian lận, đào tạo tích hợp, xử lý kỷ luật (Trang 5-9, 12, 18-20, 23).
    2. `diem_ren_luyen`: Quy chế và bảng tiêu chí tính điểm rèn luyện (Trang 10, 11, 14, 15, 16).
    3. `hoc_bong_an_sinh`: Học bổng Trần Đại Nghĩa, dự án an sinh gia sư, hệ thống eHUST (Trang 17, 21, 22).
    4. `gioi_thieu_vien_khoa`: Lịch sử trường, Đoàn thanh niên, giới thiệu các Trường/Viện/Khoa (Trang 2, 3, 24-55).
  - *Lý do chọn:* Trường `category` phản ánh chính xác phạm vi nghiệp vụ trong trường đại học, giúp câu hỏi chuyên biệt (như học bổng hoặc rèn luyện) lọc đúng phân vùng, triệt tiêu hoàn toàn nhiễu từ các đơn vị đào tạo khác.

---

## Cấu hình và benchmark

- **Mô tả 3 cấu hình chiến lược A / B / C:**
  - **Strategy A (Fixed-size Window, Không filter):** Chia chunk theo kích thước cố định `chunk_size = 500` ký tự, độ gối đầu `overlap = 50` ký tự. Sinh ra **279 chunks**. Gắn metadata đầy đủ nhưng không áp dụng bộ lọc khi truy xuất.
  - **Strategy B (Structure-aware Paragraph, Không filter):** Chia chunk theo ranh giới đoạn văn tự nhiên `\n\n`, gom các đoạn ngắn liền kề và cắt đoạn dài với giới hạn `max_size = 800` ký tự. Sinh ra **184 chunks**. Gắn cùng metadata, không áp dụng bộ lọc khi truy xuất.
  - **Strategy C (Structure-aware Paragraph + Metadata Filter):** Sử dụng **chính xác 184 chunks và vector của Strategy B**, nhưng kích hoạt bộ lọc SQL `@> '{"category": ...}'::jsonb` khi câu hỏi có trường filter.
  - *Tính độc lập có kiểm soát:* So sánh A–B kiểm tra tác động của phương pháp chia chunk (cố định vs theo đoạn); So sánh B–C kiểm tra độc lập tác động của việc lọc metadata trên cùng một tập vector và embedding model.

- **Bộ câu hỏi Benchmark (20 câu: 15 dev / 5 test):**
  - Lưu trữ tại `benchmark/questions.json` và tài liệu hóa tại `benchmark/README.md`.
  - Phân chia: **15 câu Dev** (`q01`–`q15`) và **5 câu Test hold-out** (`q16`–`q20`).
  - Phân loại câu hỏi đa dạng theo yêu cầu:
    - **12 câu hỏi trực tiếp (`truc_tiep`):** `q01`, `q02`, `q03`, `q05`, `q08`, `q09`, `q10`, `q11`, `q13`, `q14`, `q16`, `q20`.
    - **2 câu hỏi diễn đạt lại (`dien_dat_lai`):** `q04`, `q17`.
    - **2 câu hỏi điều kiện logic (`dieu_kien`):** `q07` (Dev) và `q18` (Test).
    - **1 câu hỏi ngoại lệ (`ngoai_le`):** `q12`.
    - **3 câu hỏi kiểm tra metadata filter (`filter_test`):** `q06`, `q15` (thuộc Dev) và `q19` (thuộc Test).
  - *Kiểm chứng evidence:* 100% 20 câu hỏi có đoạn trích `evidence_quote` đã được script tự động so khớp tồn tại chính xác nguyên văn trong trang PDF nguồn.

- **Tiêu chí chọn chiến lược chốt trước khi xem tập Test:**
  1. Ưu tiên 1: Đạt Evidence Hit@3 cao nhất trên tập Dev ($\ge 85\%$).
  2. Ưu tiên 2: Tính mạch lạc của Chunk (Coherence) cao nhất để LLM dễ đọc hiểu trọn vẹn ($\ge 1.5/2.0$).
  3. Ưu tiên 3: Tối ưu hóa tài nguyên (số lượng chunk ít hơn để giảm chi phí lưu trữ và latency).

---

## Kết quả

### Bảng 1: Hiệu năng truy xuất và tài nguyên

| Strategy | Split | Hit@1 (n/N) | Evidence Hit@3 (n/N) | Chunk count | Thời gian Ingest | Chi phí API |
|---|---|:---:|:---:|:---:|:---:|:---:|
| **Strategy A** | **Dev**<br>**Test**<br>Overall | 11/15 (73.3%)<br>5/5 (100.0%)<br>16/20 (80.0%) | 14/15 (93.3%)<br>5/5 (100.0%)<br>19/20 (95.0%) | 279 | 171.07s | \$0 |
| **Strategy B** | **Dev**<br>**Test**<br>Overall | 12/15 (80.0%)<br>4/5 (80.0%)<br>16/20 (80.0%) | 13/15 (86.7%)<br>5/5 (100.0%)<br>18/20 (90.0%) | 184 | 141.86s | \$0 |
| **Strategy C** | **Dev**<br>**Test**<br>Overall | 12/15 (80.0%)<br>4/5 (80.0%)<br>16/20 (80.0%) | 13/15 (86.7%)<br>5/5 (100.0%)<br>18/20 (90.0%) | 184 | 141.86s | \$0 |

### Bảng 2: Đánh giá chất lượng ngữ nghĩa và kiểm tra thủ công

| Strategy | Coherence TB /2 ($n=10$) | Metadata đủ & đúng ($n/N$) | Filter tuân thủ ($n/N$) | Grounding 0/1/2 (số câu) và TB /2 ($N=5$) |
|---|:---:|:---:|:---:|:---:|
| **Strategy A** | **0.8 / 2.0** | 15/15 (100%) | N/A (không bật filter) | 0 câu mức 0, 0 câu mức 1, 5 câu mức 2 $\rightarrow$ **2.0 / 2.0** |
| **Strategy B** | **2.0 / 2.0** | 15/15 (100%) | N/A (không bật filter) | 0 câu mức 0, 0 câu mức 1, 5 câu mức 2 $\rightarrow$ **2.0 / 2.0** |
| **Strategy C** | **2.0 / 2.0** | 15/15 (100%) | **3/3 (100%) ở Test**<br>**9/9 (100%) toàn bộ filter** | 0 câu mức 0, 0 câu mức 1, 5 câu mức 2 $\rightarrow$ **2.0 / 2.0** |

- **Đường dẫn dữ liệu và trace kiểm chứng:**
  - File traces chi tiết từng query: `results/traces_strategy_a.json`, `results/traces_strategy_b.json`, `results/traces_strategy_c.json`.
  - File tổng hợp benchmark: `results/benchmark_summary.json`.
  - File audit thủ công chi tiết: `results/manual_audit.json`.
  - Nhật ký thí nghiệm: `artifacts/experiment_log.csv`.
- **Cách chọn mẫu audit:**
  - *Coherence (10 mẫu):* Được chọn cố định tại 10 vị trí trang đại diện theo thứ tự số trang (`[2, 5, 6, 7, 10, 11, 12, 17, 21, 22]`) trước khi chạy benchmark, so sánh trực tiếp đoạn chunk tương ứng giữa Strategy A và B/C.
  - *Metadata (15 samples):* Purposefully selected stratified sample: 5 chunks for each configuration A, B, and C, covering all 4 categories and pages 2 to 52. The fields page, document_id, source, and category were checked against PostgreSQL; C reuses B index/chunks. `text_preview` is copied verbatim from the stored chunk and is not an independent PDF verification. Chunk IDs and samples are in `manual_audit.json`.
  - *Grounding (5 câu Test):* Đánh giá trên toàn bộ 5 câu hỏi của tập Test độc lập (`q16` đến `q20`) cho cả 3 chiến lược A, B, C.

---

## Phân tích và kết luận

- **So sánh A–B và B–C; 2 ví dụ sai cụ thể:**
  - *So sánh A vs B:* Strategy A tuy đạt Evidence Hit@3 trên Dev nhỉnh hơn (93.3% so với 86.7%) nhưng sinh ra nhiều hơn tới **51.6% số lượng chunk** (279 vs 184), làm tăng thời gian embedding và dung lượng lưu trữ. Điểm yếu chí mạng của Strategy A là **tính mạch lạc rất kém (0.8/2.0)** do cắt ngang câu/từ (ví dụ trang 2 cắt cụt từ `trư`, trang 10 cắt cụt `Trách nhiệm tham gia c`). Strategy B giải quyết triệt để vấn đề này, đạt điểm mạch lạc tối đa **2.0/2.0** và tăng Hit@1 trên Dev từ 73.3% lên 80.0%.
  - *So sánh B vs C:* B và C có cùng Hit@3 trên tập benchmark hiện tại vì tập corpus 55 trang chưa quá lớn. Tuy nhiên, ở các câu hỏi kiểm tra filter (như `q06`, `q15`, `q19`), Strategy C kích hoạt bộ lọc metadata SQL và đảm bảo **100% các chunks trong Top-3 đều thuộc đúng danh mục quy định**, ngăn chặn triệt để hiện tượng câu hỏi về học bổng lại bị lọt các chunk giới thiệu khoa/viện có chứa các từ khóa tương đồng.
  - *Ví dụ sai 1 (`q13` - Trượt Hit@3 trên cả A, B, C):*
    - Câu hỏi: *"Theo thống kê của Dự án An sinh, tỷ lệ sinh viên có nguyện vọng hoặc từng làm gia sư là bao nhiêu?"* (Gold: Trang 21).
    - Phân tích: Cả 3 cấu hình đều xếp các đoạn văn về NCKH và tư vấn học tập ở Trang 13 và 22 lên trước Trang 21. Lý do: Mô hình embedding ngữ nghĩa coi cụm từ "thống kê", "nguyện vọng" gần với các chủ đề tư vấn định hướng chung hơn là thông tin về dự án gia sư cụ thể.
  - *Ví dụ sai 2 (`q09` - Strategy A đúng Hit@1, nhưng Strategy B & C trượt Hit@3):*
    - Câu hỏi: *"Theo quy chế có bao nhiêu hình thức xử lý kỷ luật sinh viên?"* (Gold: Trang 12).
    - Phân tích: Ở Strategy B, đoạn văn trang 12 chỉ vỏn vẹn 160 ký tự (danh sách 4 hình thức kỷ luật). Đoạn quá ngắn làm mật độ vector bị loãng khi so sánh cosine với các đoạn văn dài giải thích hành vi vi phạm ở trang 6. Ngược lại, cửa sổ 500 ký tự của Strategy A tình cờ gom thêm các câu xung quanh giúp vector của trang 12 nổi bật hơn. Đây là **trade-off kinh điển**: *Chunking theo đoạn văn tự nhiên dễ gặp rủi ro đoạn cụt (stub paragraphs)*.

- **Chiến lược được chọn, đánh đổi và điều kiện áp dụng:**
  - *Chiến lược được chọn:* **Strategy C (hoặc Strategy B khi không có filter sẵn)**.
  - *Lý do:* Đạt điểm Coherence vượt trội (2.0/2), tiết kiệm 34% số lượng chunk so với A, Hit@1 cao (80%), và bảo đảm an toàn dữ liệu nhờ metadata filter.
  - *Đánh đổi:* Chấp nhận nguy cơ một số đoạn văn quá ngắn có thể bị giảm semantic density.
  - *Điều kiện áp dụng:* Phù hợp nhất cho hệ thống RAG tra cứu văn bản quy chế, pháp quy, sổ tay sinh viên hoặc cẩm nang tổ chức nơi văn bản được biên soạn theo cấu trúc điều khoản rõ ràng.

- **Hạn chế của dữ liệu, nhãn, tập test nhỏ và đo lường:**
  - *Kích thước tập test:* Tập test 5 câu là mức tối thiểu của bài lab, tuy đủ kiểm chứng tính nhất quán nhưng biên độ sai số thống kê còn cao (mỗi câu chiếm 20%).
  - *Đánh giá thủ công:* Người đánh giá là tác giả nên có nguy cơ thiên lệch chủ quan nhẹ, dù đã cố gắng bám sát rubric và kiểm chứng văn bản nguyên bản.
  - *Đo thời gian:* Thời gian chạy phụ thuộc vào độ trễ mạng internet và cơ chế rate-limit 429 của dịch vụ API miễn phí.

- **Nếu làm lại hoặc mở rộng, cải tiến những gì?**
  1. *Cải tiến chunking (Hybrid Merge):* Bổ sung luật tự động gộp các đoạn văn quá ngắn ($< 250$ ký tự) vào đoạn liền kề để tránh lỗi "đoạn cụt" như ở câu `q09`.
  2. *Hybrid Retrieval:* Kết hợp Dense Vector Search với BM25 (Sparse Keyword Search) để xử lý hoàn hảo các câu hỏi chứa con số và tỷ lệ chính xác (như `30%`, `4 hình thức`, `848 sinh viên`).
  3. *Tự động sinh Metadata Filter bằng LLM:* Xây dựng module trích xuất tự động `filter` từ câu hỏi tự nhiên của người dùng trước khi gọi database truy xuất.
