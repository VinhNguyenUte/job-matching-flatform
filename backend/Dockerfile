# ==================== BACKEND - FastAPI ====================
FROM python:3.12-slim

# Thiết lập thư mục làm việc
WORKDIR /app

# Cài đặt dependencies hệ thống
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để tận dụng cache Docker layer
COPY requirements.txt .

# Cài đặt Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ source code
COPY . .

# Expose port
EXPOSE 8000

# Command để chạy (sẽ override trong docker-compose cho dev)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]