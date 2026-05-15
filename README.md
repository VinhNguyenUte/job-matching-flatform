cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
alembic upgrade head

cd ..
docker compose up -d --build

# Xem log backend
docker compose logs -f backend

# Xem log celery
docker compose logs -f celery-worker

# Restart tất cả
docker compose restart

# Dừng project
docker compose down

# Dừng + xóa database (reset)
docker compose down -v
