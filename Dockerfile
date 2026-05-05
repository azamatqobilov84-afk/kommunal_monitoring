FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Tizim paketlari (PostgreSQL, build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Python kutubxonalari (kesh uchun alohida qatlam)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Loyiha kodlari
COPY . .

# Static fayllarni yig'ish
RUN python manage.py collectstatic --noinput

# Volume papkasi (db.sqlite3 va media uchun)
RUN mkdir -p /data/media

EXPOSE 8000

# Boshlash buyrug'i: migrate + seed (xavfsiz) + gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_data && gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 2 --access-logfile -"]
