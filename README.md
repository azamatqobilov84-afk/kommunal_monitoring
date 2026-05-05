# 🏠 Kommunal to'lovlar monitoringi

> Click stilida zamonaviy Django web ilova — kommunal xizmatlar uchun monitoring va to'lov tizimi.

O'zbekistondagi mashhur Click ilovasiga o'xshash interfeys va imkoniyatlar bilan, ammo
asosiy e'tibor — gaz, elektr, suv, issiqlik, internet va mobil aloqa kabi
kommunal xizmatlarning sarflanishini kuzatish, ortiqcha sarfni avtomatik aniqlash va
to'lovlarni tezkor amalga oshirishga qaratilgan.

---

## ✨ Asosiy imkoniyatlar

- 📱 **Telefon orqali ro'yxatdan o'tish** — mock SMS tasdiqlash bilan
- 💳 **Mock to'lov tizimi** — UzCard, Humo, Visa kartalari (haqiqiy pul yechilmaydi)
- 🏘️ **Bir nechta manzillar** — har bir uy/ofis/dacha uchun alohida hisob
- 🔢 **Hisoblagichlar** — elektr, gaz, suv, issiqlik uchun
- 📊 **Statistika va grafiklar** — Chart.js bilan oylik/yillik tahlil
- ⚠️ **Anomaliya aniqlash** — sarf keskin oshganda avtomatik ogohlantirish
   (Z-score va o'rtachadan og'ish algoritmlari bilan)
- 🔔 **Bildirishnomalar** — to'lov muddatlari, anomaliyalar, yangi tariflar
- 🔁 **Avtomatik to'lovlar** — har oy belgilangan kunda
- ⏰ **Eslatmalar** — to'lovlarni unutmaslik uchun
- 👨‍👩‍👧 **Oila a'zolari** — bir manzilni birga boshqarish
- 📄 **Hisobotlar va kvitansiyalar** — chop etish/PDF
- 🌐 **Mobil-first dizayn** — Click stilida ko'k gradient

---

## 🛠 Texnologiyalar

| Soha | Vosita |
|------|--------|
| Backend | Python 3.10+, Django 5.0 |
| Database | SQLite (mahalliy) |
| Frontend | Bootstrap 5 + Bootstrap Icons |
| Grafiklar | Chart.js (CDN orqali) |
| Rasmlar | Pillow |

Hech qanday tashqi pulli API talab qilinmaydi — barcha to'lovlar va SMS **mock rejimda** ishlaydi.

---

## 🚀 O'rnatish va ishga tushirish

### 1. Loyihani yuklab oling

```bash
unzip kommunal_monitoring.zip
cd kommunal_monitoring
```

### 2. Virtual muhit yarating

```bash
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Kutubxonalarni o'rnating

```bash
pip install -r requirements.txt
```

### 4. Ma'lumotlar bazasini yarating

```bash
python manage.py migrate
```

### 5. Test ma'lumotlarini yuklang

```bash
python manage.py seed_data
```

### 6. (Ixtiyoriy) Admin foydalanuvchi yarating

```bash
python manage.py createsuperuser
```

### 7. Serverni ishga tushiring

```bash
python manage.py runserver
```

Brauzerda oching: **http://127.0.0.1:8000/**

---

## 🔐 Test foydalanuvchilar

Seed buyrug'i quyidagi foydalanuvchilarni avtomatik yaratadi:

| Ism | Telefon | Parol |
|-----|---------|-------|
| Akmal Karimov | `+998901234567` | `parol12345` |
| Madina Yusupova | `+998937654321` | `parol12345` |

> **Akmal**ning hisobida sun'iy ravishda yuqori sarfli oy yaratilgan — bu
> sizga **anomaliya aniqlash funksiyasini** darhol ko'rish imkonini beradi.

### Mock SMS

Ro'yxatdan o'tish va parol tiklashdagi SMS kodlar **terminalga chop etiladi**.
Kodni shu yerdan ko'ring va kiriting.

---

## 📁 Loyiha tuzilishi

```
kommunal_monitoring/
├── config/                  # Django sozlamalari
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── core/                    # Asosiy ilova
│   ├── models.py            # 14 ta ma'lumot modeli
│   ├── views.py             # Barcha sahifalar
│   ├── forms.py             # Formalar
│   ├── urls.py              # URL marshrutlari
│   ├── admin.py             # Admin panel sozlamalari
│   ├── utils.py             # Anomaliya aniqlash algoritmlari
│   ├── context_processors.py
│   └── management/commands/
│       └── seed_data.py     # Test ma'lumot generator
├── templates/               # 30+ ta HTML shablon
│   ├── base.html
│   ├── dashboard.html
│   ├── auth/                # Kirish, ro'yxatdan o'tish
│   ├── properties/          # Manzillar
│   ├── meters/              # Hisoblagichlar
│   ├── transactions/        # To'lovlar va kvitansiyalar
│   ├── cards/               # Bank kartalari
│   ├── payments/            # To'lov yaratish
│   ├── notifications/       # Bildirishnomalar
│   ├── anomalies/           # Anomaliyalar
│   ├── reminders/           # Eslatmalar
│   ├── auto_payments/       # Avto-to'lovlar
│   ├── family/              # Oila a'zolari
│   ├── statistics.html
│   ├── reports.html
│   ├── tariffs.html
│   ├── profile.html
│   └── settings.html
├── static/css/app.css       # Click stilida CSS
├── media/                   # Yuklangan fayllar (avatar, hisoblagich rasmlari)
├── manage.py
├── requirements.txt
└── README.md
```

---

## 🌐 Asosiy URL'lar

| URL | Tavsif |
|-----|--------|
| `/` | Lending sahifa |
| `/register/` | Telefon orqali ro'yxat |
| `/login/` | Kirish |
| `/dashboard/` | Asosiy boshqaruv paneli |
| `/properties/` | Manzillarim |
| `/properties/<id>/` | Manzil tafsilotlari va hisoblagichlari |
| `/meters/<id>/reading/new/` | Yangi ko'rsatkich kiritish |
| `/meters/<id>/history/` | Hisoblagich tarixi va grafigi |
| `/payments/new/` | Yangi to'lov |
| `/payments/<service-slug>/` | Aniq xizmat uchun to'lov |
| `/transactions/` | Barcha tranzaksiyalar (filtr + qidiruv) |
| `/transactions/export/` | CSV eksport |
| `/transactions/<id>/receipt/` | Kvitansiya (chop etiladi) |
| `/cards/` | Bank kartalari |
| `/statistics/` | Statistika va grafiklar |
| `/anomalies/` | Anomaliyalar ro'yxati |
| `/notifications/` | Bildirishnomalar |
| `/reminders/` | Eslatmalar |
| `/auto-payments/` | Avtomatik to'lovlar |
| `/reports/` | Yillik/oylik hisobotlar |
| `/family/` | Oila a'zolari |
| `/tariffs/` | Joriy tariflar |
| `/settings/` | Sozlamalar |
| `/admin/` | Django admin paneli |

---

## 🌐 Bepul serverga yuklash (Deploy)

Loyiha **3 ta bepul platformaga** yuklash uchun tayyorlangan:

| Platforma | Karta kerakmi | Eng yaxshi tomoni |
|-----------|---------------|-------------------|
| **Render.com** | ❌ Yo'q | Eng oson, GitHub auto-deploy |
| **Fly.io** | ✅ Ha | Doim ishlaydi (uxlamaydi) |
| **Railway** | ✅ Ha | Eng tez setup |

To'liq qadamma-qadam yo'riqnoma uchun **[DEPLOY.md](DEPLOY.md)** faylini oching.

Loyihada quyidagi production fayllari avtomatik tayyorlangan:
- `requirements.txt` — gunicorn, whitenoise, dj-database-url, psycopg2-binary
- `build.sh` — Render uchun build skripti
- `Dockerfile` + `.dockerignore` — Fly.io uchun
- `fly.toml` — Fly.io konfiguratsiya
- `railway.json` — Railway konfiguratsiya
- `Procfile` + `runtime.txt` — universal
- `.env.example` — environment variables namunasi

---

## 🎯 Qanday sinab ko'rish kerak

1. **Kirish:** `+998901234567` / `parol12345`
2. **Bosh sahifada:** balansingizni, oxirgi to'lovlaringizni, anomaliya bannerlarini ko'rasiz
3. **Manzillar →** "Asosiy uy" → uchta hisoblagich (elektr, gaz, suv) bor
4. **Elektr hisoblagichi → Tarix** — Chart.js grafigida sarf dinamikasi
5. **Yangi ko'rsatkich kiritish** — sarfni avtomatik hisoblaydi va anomaliya aniqlaydi
6. **Statistika** — 4 ta turli grafik:
    - Oylik xarajatlar (line)
    - Bu oy taqsimoti (doughnut)
    - Bu oy vs O'tgan oy vs O'tgan yil (bar)
    - Xizmatlar bo'yicha ko'p chiziqli grafik
7. **Anomaliyalar** — Akmalning elektr hisoblagichida 1 ta yuqori sarfli oy bor
8. **Yangi to'lov →** xizmat tanlang → karta tanlang → to'lov amalga oshadi (mock)
9. **Tranzaksiyalar →** filtr, qidiruv, CSV eksport, kvitansiya → chop etish
10. **Karta qo'shish** — UzCard/Humo/Visa, oxirgi 4 raqam ko'rinadi
11. **Eslatmalar** va **Avto-to'lovlar** sozlash
12. **Oila a'zolari** — Madinani Akmalga a'zo qilib qo'shish

---

## 🧪 Anomaliya aniqlash algoritmlari

Tizim hisoblagich ko'rsatkichi kiritilganda quyidagilarni avtomatik aniqlaydi:

1. **Xato kiritish** — joriy ko'rsatkich avvalgisidan kichik bo'lsa
2. **Keskin oshish** — oxirgi 3 oy o'rtachasidan 30% (sozlanuvchi) ortiq sarf
3. **Statistik anomaliya** — Z-score | > 2.5 (5+ yozuv bo'lganida)

Anomaliya aniqlanganda:
- Yozuv `is_anomaly=True` deb belgilanadi
- Bildirishnoma yaratiladi
- Dashboard'da qizil banner ko'rinadi
- `/anomalies/` sahifasida ro'yxatga tushadi

---

## 🔒 Xavfsizlik

- ✅ CSRF himoyasi barcha formalarda
- ✅ `@login_required` dekoratorlari maxfiy sahifalarda
- ✅ Foydalanuvchi faqat **o'zining** ma'lumotlarini ko'radi (queryset filter)
- ✅ Karta raqamlari to'liq saqlanmaydi — faqat oxirgi 4 raqam
- ✅ Parollar PBKDF2 bilan hash qilinadi (Django default)
- ✅ Admin panel `is_staff` orqali himoyalangan
- ✅ Django ORM SQL injection'dan, template engine XSS'dan himoya qiladi

---

## 📊 Database modellari (14 ta)

| Model | Tavsif |
|-------|--------|
| `User` | Telefon raqami username sifatida |
| `Property` | Manzillar (uy/dacha/ofis) |
| `Service` | Xizmat turlari (gaz, elektr, ...) |
| `Tariff` | Tarif rejalari (vaqt va hudud bo'yicha) |
| `Meter` | Hisoblagichlar |
| `MeterReading` | Hisoblagich ko'rsatkichlari |
| `Card` | Mock bank kartalari |
| `Transaction` | To'lovlar |
| `Notification` | Bildirishnomalar |
| `Reminder` | Eslatmalar |
| `AutoPayment` | Avtomatik to'lov rejalari |
| `Anomaly` | Aniqlangan anomaliyalar |
| `FamilyMember` | Oila a'zolari (manzil ulashish) |
| `SmsCode` | Mock SMS tasdiqlash kodlari |

---

## 🎨 Dizayn

- **Asosiy ranglar:** Click stilida ko'k gradient (#0066ff → #00aaff)
- **Yumshoq fonlar:** #f5f7fb
- **Yumaloq burchaklar:** 12-20px radius
- **Yengil soyalar:** 2-8px shadow
- **Mobil-first:** mobilda pastki navigation 5 ta tugma bilan
- **Bootstrap Icons:** rangli, dumaloq fonli ikonkalar
- **Chart.js:** doughnut, line, bar grafiklari

---

## 📝 Litsenziya

Demo loyiha — o'rganish va ko'rsatish uchun yaratilgan.
Barcha to'lovlar **mock rejimda** ishlaydi — haqiqiy pul yechilmaydi.

---

> 💙 Yaratildi: Django 5.0 + Bootstrap 5 + Chart.js
