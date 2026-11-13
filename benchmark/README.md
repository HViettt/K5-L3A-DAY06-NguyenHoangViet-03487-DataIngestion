# Bộ câu hỏi Benchmark (20 câu)

Tập dữ liệu câu hỏi đánh giá hệ thống Ingestion & Retrieval dựa trên Sổ tay Sinh viên 2026 (`data/so_tay_sinh_vien_2026.pdf`).

## Phân chia tập dữ liệu (Splits)
- **Tập Dev (15 câu):** `q01` đến `q15`. Dùng để tinh chỉnh chiến lược và kiểm thử ban đầu.
- **Tập Test (5 câu):** `q16` đến `q20`. Tập hold-out độc lập để đánh giá cuối cùng.
- **Câu hỏi kiểm tra Metadata Filter (3 câu):** `q06`, `q15` (thuộc Dev) và `q19` (thuộc Test).
- **Câu hỏi Điều kiện (2 câu):** `q07` (Dev) và `q18` (Test).

## Danh sách 20 câu hỏi

| ID | Split | Phân loại | Trang Gold | Metadata Filter | Câu hỏi |
|---|---|---|:---:|---|---|
| `q01` | Dev | Trực tiếp | 2 | - | Trường ĐHBK Hà Nội thành lập theo nghị định nào và vào ngày tháng năm nào? |
| `q02` | Dev | Trực tiếp | 2 | - | Lễ khai giảng khóa 1 có bao nhiêu sinh viên trúng tuyển? |
| `q03` | Dev | Trực tiếp | 5 | - | Sinh viên đến trường cần mang theo vật dụng gì và yêu cầu trang phục thế nào? |
| `q04` | Dev | Diễn đạt lại | 6 | - | Những hành vi gian lận nào trong học tập và thi cử bị nghiêm cấm? |
| `q05` | Dev | Trực tiếp | 7 | - | Mô hình đào tạo tích hợp chính quy có tổng thời gian đào tạo chuẩn là bao lâu? |
| `q06` | Dev | Filter | 10 | `diem_ren_luyen` | Kết quả rèn luyện được sử dụng cho những mục đích nào? |
| `q07` | Dev | Điều kiện | 10 | - | Không tự đánh giá rèn luyện và không có lý do chính đáng bị xếp loại gì? |
| `q08` | Dev | Trực tiếp | 11 | - | Tiêu chí 1 về chấp hành pháp luật/nội quy rèn luyện có điểm tối đa bao nhiêu? |
| `q09` | Dev | Trực tiếp | 12 | - | Có bao nhiêu hình thức xử lý kỷ luật sinh viên theo quy chế? |
| `q10` | Dev | Trực tiếp | 17 | - | Học bổng Trần Đại Nghĩa được xét cấp cho đối tượng sinh viên nào? |
| `q11` | Dev | Trực tiếp | 17 | - | Học bổng Trần Đại Nghĩa có những mức hỗ trợ học phí nào? |
| `q12` | Dev | Ngoại lệ | 17 | - | Sinh viên bị kỷ luật từ mức nào trở lên thì không được xét cấp học bổng Trần Đại Nghĩa? |
| `q13` | Dev | Trực tiếp | 21 | - | Tỷ lệ sinh viên có nguyện vọng làm gia sư theo Dự án An sinh là bao nhiêu? |
| `q14` | Dev | Trực tiếp | 22 | - | Hệ thống quản trị trực tuyến eHUST triển khai từ năm học nào? |
| `q15` | Dev | Filter | 31 | `gioi_thieu_vien_khoa` | Trường Điện - Điện tử gồm bao nhiêu khoa trực thuộc và bao nhiêu giảng viên? |
| `q16` | Test | Trực tiếp | 35 | - | Khoa Ngoại ngữ có bao nhiêu cán bộ và có bao nhiêu Tiến sĩ? |
| `q17` | Test | Diễn đạt lại | 5 | - | Khi lái xe máy/ô tô vào khuôn viên trường, sinh viên phải tuân thủ điều gì? |
| `q18` | Test | Điều kiện | 10 | - | Mức điểm rèn luyện bao nhiêu thì được xếp loại Xuất sắc và loại Tốt? |
| `q19` | Test | Filter | 17 | `hoc_bong_an_sinh` | Học bổng Trần Đại Nghĩa được xét và cấp với tần suất như thế nào? |
| `q20` | Test | Trực tiếp | 27 | - | Việc cấp lại sổ đoàn và ký thanh toán ra trường thực hiện tại đâu? |

Tất cả 20 đoạn trích dẫn chứng (`evidence_quote`) đã được kiểm chứng khớp 100% với văn bản thực tế trong file PDF.
