# 1. Chốt bản bookworm để đảm bảo Playwright hỗ trợ cài dependencies chuẩn
FROM python:3.10-slim-bookworm

# Thiết lập thư mục làm việc
WORKDIR /app

# Thiết lập biến môi trường
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HEADLESS=true

# Copy file requirements và cài đặt python dependencies TRƯỚC
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install xvfb to run headed browser in docker
RUN apt-get update && apt-get install -y xvfb && rm -rf /var/lib/apt/lists/*

# 2. Cài Chromium của Playwright VÀ các thư viện đi kèm của nó bằng 1 lệnh duy nhất
RUN playwright install --with-deps chromium

# Copy toàn bộ mã nguồn crawler vào container
COPY . .

# Tạo thư mục data để lưu trữ kết quả cào dữ liệu
RUN mkdir -p data

# Chạy Xvfb ở background và set DISPLAY, sau đó chạy python để không bị mất log
CMD Xvfb :99 -screen 0 1280x800x24 & export DISPLAY=:99 && python cronjob.py