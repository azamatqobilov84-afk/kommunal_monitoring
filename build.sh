#!/usr/bin/env bash
# Render.com va shu turdagi platformalar uchun build skripti
# Bu skript loyiha har deploy bo'lganida bir marta ishlaydi
set -o errexit

echo "📦 Kutubxonalarni o'rnatish..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🎨 Static fayllarni yig'ish..."
python manage.py collectstatic --no-input --clear

echo "🗄️  Ma'lumotlar bazasini migratsiya qilish..."
python manage.py migrate --noinput

echo "🌱 Test ma'lumotlarini yuklash (faqat birinchi safar)..."
python manage.py seed_data || true

echo "✅ Build muvaffaqiyatli yakunlandi!"
