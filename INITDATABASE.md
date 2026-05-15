# Run JD Database Ingestion

File này hướng dẫn chạy riêng phần nhận JD thô, gọi AI xử lý và insert vào PostgreSQL.

## 1. Chuẩn Bị `.env`

Tạo file `.env` ở root project từ `.env.example`.

Các biến tối thiểu cần có:

```env
POSTGRES_DB=job_matching_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password
POSTGRES_HOST=db
POSTGRES_PORT=5432

GEMINI_API_KEY=your_gemini_api_key_here

AI_SERVICE_URL=http://ai-service:8001
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Ghi chú:

- Khi chạy bằng Docker Compose, `POSTGRES_HOST=db` là đúng.
- Khi chạy backend ngoài Docker và DB trong Docker, dùng `POSTGRES_HOST=localhost`, `POSTGRES_PORT=5433`.
- `AI_SERVICE_URL=http://ai-service:8001` dùng cho backend gọi AI service trong Docker network.

## 2. Build Và Chạy Container

Từ root project:

```bash
docker compose up -d --build
```

Kiểm tra container:

```bash
docker compose ps
```

Các service liên quan cần chạy:

```text
db
ai-service
backend
frontend
```

## 3. Init Database Schema

Sau khi `db` và `backend` đã chạy, tạo schema JD:

```bash
docker compose exec backend python init_db.py
```

Nếu muốn reset toàn bộ bảng JD rồi tạo lại:

```bash
docker compose exec backend python init_db.py --reset
```

Schema được tạo từ:

```text
backend/sql/schema.sql
```

## 4. Kiểm Tra Health

Backend:

```bash
curl http://localhost:8000/health
```

AI service:

```bash
curl http://localhost:8001/health
```

Kỳ vọng đều trả về `status: ok`.

## 5. Test Preview JD

Endpoint preview chỉ gọi AI parse JD, chưa insert DB.

```bash
curl -X POST http://localhost:8000/jobs/preview \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "Backend Developer",
      "company": "Example Tech",
      "location": "Ho Chi Minh",
      "post_time": "2026-05-16",
      "link": "https://example.com/jobs/backend-developer",
      "description": "We are looking for a Backend Developer with Python, FastAPI, PostgreSQL, Docker, Git. Minimum 2 years of experience. English communication is preferred. Hybrid working mode."
    }
  ]'
```

Nếu thành công, response sẽ là JSON đã được AI chuẩn hóa theo schema.

## 6. Test Ingest JD Vào Database

Endpoint ingest sẽ:

- kiểm tra trùng `source_url`
- kiểm tra trùng `content_hash`
- ghi `job_raw_logs`
- gọi AI service để parse và tạo embedding
- insert vào các bảng domain

```bash
curl -X POST http://localhost:8000/jobs/ingest \
  -H "Content-Type: application/json" \
  -d '[
    {
      "title": "Backend Developer",
      "company": "Example Tech",
      "location": "Ho Chi Minh",
      "post_time": "2026-05-16",
      "link": "https://example.com/jobs/backend-developer",
      "description": "We are looking for a Backend Developer with Python, FastAPI, PostgreSQL, Docker, Git. Minimum 2 years of experience. English communication is preferred. Hybrid working mode."
    }
  ]'
```

Response thành công sẽ có dạng:

```json
{
  "success": true,
  "summary": {
    "total": 1,
    "success": 1,
    "skipped": 0,
    "errors": 0
  },
  "results": [
    {
      "title": "Backend Developer",
      "status": "success",
      "job_id": 1,
      "detail": null
    }
  ]
}
```

Nếu chạy lại cùng `link` hoặc cùng `description`, hệ thống có thể trả `skipped`.

## 7. Kết Nối PostgreSQL Docker Để Xem Dữ Liệu

Bạn có thể dùng pgAdmin, DBeaver hoặc DataGrip để kết nối vào PostgreSQL container.

Thông tin kết nối từ máy host:

```text
Host: localhost
Port: 5433
Database: job_matching_db
Username: user
Password: password
Schema: public
```

Giải thích port:

```yaml
ports:
  - "5433:5432"
```

Nghĩa là PostgreSQL chạy trong container ở port `5432`, nhưng máy host kết nối qua port `5433`.

Nếu tool/database client chạy trong cùng Docker network, dùng:

```text
Host: db
Port: 5432
```

Sau khi connect, refresh schema `public`. Nếu chưa thấy bảng, chạy init schema trước:

```bash
docker compose exec backend python init_db.py
```

Các query kiểm tra nhanh trong Query Tool:

```sql
SELECT current_database(), current_schema();

SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;

SELECT id, name FROM companies ORDER BY id DESC LIMIT 5;

SELECT id, title, company_id, source_url, created_at
FROM jobs
ORDER BY id DESC
LIMIT 5;

SELECT id, source_url, processing_status, scraped_at
FROM job_raw_logs
ORDER BY id DESC
LIMIT 5;

SELECT s.name, js.priority_level
FROM job_skills js
JOIN skills s ON s.id = js.skill_id
ORDER BY js.job_id DESC
LIMIT 20;
```

Nếu query báo kiểu `object could not be found`, thường là một trong các nguyên nhân sau:

- Bạn đang connect nhầm database, hãy chọn `job_matching_db`.
- Chưa chạy `docker compose exec backend python init_db.py`.
- Chưa refresh lại schema `public` sau khi init.
- Đang dùng sai port, từ máy host phải dùng `5433`, không phải `5432`.

## 8. Xem Logs Khi Có Lỗi

Backend:

```bash
docker compose logs -f backend
```

AI service:

```bash
docker compose logs -f ai-service
```

Database:

```bash
docker compose logs -f db
```

## 9. Các File Chính Của Flow Này

Backend:

```text
backend/init_db.py
backend/sql/schema.sql
backend/app/models/
backend/app/services/jd_ingestion.py
backend/app/api/v1/job.py
backend/app/clients/ai_service_client.py
```

AI service:

```text
ai_service/app/features/jd_ingestion/router.py
ai_service/app/features/jd_ingestion/service.py
ai_service/app/features/jd_ingestion/parser.py
ai_service/app/features/jd_ingestion/embedder.py
ai_service/app/common/clients/gemini.py
```

## 10. Reset Môi Trường

Dừng container:

```bash
docker compose down
```

Dừng và xóa volume database:

```bash
docker compose down -v
```

Sau khi xóa volume, cần chạy lại:

```bash
docker compose up -d --build
docker compose exec backend python init_db.py
```

## SUPER SET UP

Chạy toàn bộ service bằng Docker Compose: `docker compose up -d --build`

Kiểm tra trạng thái container: `docker compose ps`

Tạo database schema lần đầu: `docker compose exec backend python init_db.py`

Kết nối pgAdmin4/DBeaver vào PostgreSQL Docker: `Host=localhost; Port=5433; Database=job_matching_db; Username=user; Password=password; Schema=public`

Mở API docs của backend để nhập test: `http://localhost:8000/docs`

Mở API docs của AI service nếu cần test riêng AI: `http://localhost:8001/docs`

Test preview JD, chỉ parse bằng AI và chưa insert DB: `POST http://localhost:8000/jobs/preview`

Test ingest JD, parse bằng AI và insert DB: `POST http://localhost:8000/jobs/ingest`

Kiểm tra dữ liệu jobs sau khi insert: `SELECT * FROM public.jobs ORDER BY id ASC LIMIT 100`

Reset backend khi sửa code backend: `docker compose restart backend`

Reset AI service khi đổi `GEMINI_API_KEY`: `docker compose restart ai-service`

Reset schema JD về trạng thái init và xóa dữ liệu cũ: `docker compose exec backend python init_db.py --reset`

Reset sạch toàn bộ database volume: `docker compose down -v`

Chạy lại sau khi reset sạch volume: `docker compose up -d --build && docker compose exec backend python init_db.py`