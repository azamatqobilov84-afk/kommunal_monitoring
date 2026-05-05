# 🚀 Deploy yo'riqnomasi — Render / Fly.io / Railway

Bu loyiha **uchchala bepul platformaga ham** yuklash uchun tayyorlangan.

> ✅ Loyihada barcha kerakli production fayllari mavjud:
> `requirements.txt`, `build.sh`, `Dockerfile`, `fly.toml`, `railway.json`, `Procfile`, `runtime.txt`

---

## 📝 Avval — barcha platformalar uchun umumiy qadamlar

### A) `DJANGO_SECRET_KEY` yaratish

Terminalda:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

Chiqqan satrni **saqlab qo'ying** — har 3 platformada kerak bo'ladi.

### B) GitHub ga loyihani yuklash (Render va Railway uchun majburiy)

```bash
cd kommunal_monitoring
git init
git add .
git commit -m "Birinchi yuklov"
```

GitHub da yangi **bo'sh** repository yarating: https://github.com/new
- Name: `kommunal-monitoring`
- ⚠️ README/license qo'shmang (bo'sh bo'lsin)

So'ng (USERNAME ni almashtiring):

```bash
git branch -M main
git remote add origin https://github.com/USERNAME/kommunal-monitoring.git
git push -u origin main
```

> 💡 **Login parol o'rniga Personal Access Token kerak:**
> GitHub → Settings → Developer settings → Personal access tokens → Generate new (classic) → `repo` ruxsatini bering.

---

## 🌐 1. RENDER.COM (eng oson, kartasiz)

### Qadam 1: Ro'yxatdan o'tish
- https://render.com → "Sign up with GitHub"
- GitHub avtorizatsiyasi

### Qadam 2: PostgreSQL bazasi yaratish (avval baza!)
1. Dashboard → **"+ New"** → **"PostgreSQL"**
2. Sozlamalar:
   - **Name:** `kommunal-db`
   - **Region:** `Frankfurt` (Toshkentga eng yaqin)
   - **Plan:** `Free`
3. **"Create Database"** ni bosing → ~2 daqiqa kuting
4. Yaratilgach, **"Internal Database URL"** ni nusxalang (keyingi qadamda kerak)

### Qadam 3: Web Service yaratish
1. Dashboard → **"+ New"** → **"Web Service"**
2. GitHub repository (`kommunal-monitoring`) → **"Connect"**
3. Sozlamalar:
   | Maydon | Qiymat |
   |--------|--------|
   | Name | `kommunal-monitoring` |
   | Region | `Frankfurt` (baza bilan bir xil!) |
   | Branch | `main` |
   | Runtime | `Python 3` |
   | Build Command | `./build.sh` |
   | Start Command | `gunicorn config.wsgi:application` |
   | Plan | `Free` |

### Qadam 4: Environment Variables qo'shish
Pastga tushib **"Advanced"** → **"Add Environment Variable"**:

| Key | Value |
|-----|-------|
| `RENDER` | `True` |
| `DJANGO_SECRET_KEY` | (yuqorida yaratilgan kalit) |
| `DATABASE_URL` | (Internal Database URL) |
| `PYTHON_VERSION` | `3.11.0` |

### Qadam 5: Deploy
**"Create Web Service"** → 5-10 daqiqa kuting

✅ Tayyor: `https://kommunal-monitoring.onrender.com`

### Yangilash
```bash
git add . && git commit -m "yangilash" && git push
```
Render avtomatik deploy qiladi.

### ⚠️ Render eslatmalar
- 15 daqiqa harakatsizlikdan keyin uxlaydi (keyingi so'rov ~30 sek kutadi)
- Bepul PostgreSQL **90 kunda o'chiriladi** (email keladi, vaqtida backup qiling)

---

## 🚀 2. FLY.IO (doim ishlaydi, lekin karta kerak)

### Qadam 1: Ro'yxatdan o'tish
1. https://fly.io/app/sign-up → email + parol
2. **Billing** → kredit karta qo'shing
3. **Spending limit:** `$0` qo'ying (pul yechilmasligi uchun)

### Qadam 2: `flyctl` (CLI) o'rnatish

**Windows (PowerShell):**
```powershell
iwr https://fly.io/install.ps1 -useb | iex
```

**Linux/macOS:**
```bash
curl -L https://fly.io/install.sh | sh
```

Terminalni **yopib qayta oching** va tekshiring:
```bash
flyctl version
```

### Qadam 3: Login
```bash
flyctl auth login
```
Brauzer ochiladi → tasdiqlang.

### Qadam 4: App yaratish
Loyiha papkasida:
```bash
flyctl launch --no-deploy
```

**Savollarga javoblar:**
| Savol | Javob |
|-------|-------|
| Use existing fly.toml? | **Yes** (loyihada bor) |
| App name | (loyihada `kommunal-monitoring` — agar band bo'lsa: `kommunal-monitoring-USERNAME`) |
| Region | `fra` (Frankfurt) |
| Postgres database? | **No** (SQLite ishlatamiz) |
| Redis? | **No** |
| Deploy now? | **No** |

### Qadam 5: Volume yaratish (ma'lumotlar yo'qolmasligi uchun)
```bash
flyctl volumes create kommunal_data --region fra --size 1
```
Tasdiqlang: **`y`**

### Qadam 6: Secret qo'shish
```bash
flyctl secrets set DJANGO_SECRET_KEY="yuqorida-yaratilgan-secret-key"
```

### Qadam 7: Deploy
```bash
flyctl deploy
```
5-10 daqiqa kuting. Tayyor bo'lganda:
```bash
flyctl open
```

✅ Brauzer ochiladi: `https://kommunal-monitoring.fly.dev`

### Yangilash
```bash
git add . && git commit -m "yangilash" && git push
flyctl deploy
```

### Foydali Fly.io buyruqlar
```bash
flyctl logs           # Real-time loglar
flyctl status         # Holat
flyctl ssh console    # Serverga SSH
flyctl secrets list   # Maxfiy o'zgaruvchilar
flyctl scale memory 512  # Xotira oshirish
```

---

## 🚂 3. RAILWAY (eng tez setup, $5 kredit/oy)

### Qadam 1: Ro'yxatdan o'tish
1. https://railway.app/login
2. **"Login with GitHub"** → avtorizatsiya
3. (Trial tugagach) Profil → **Plans** → kredit karta

### Qadam 2: Project yaratish
1. Dashboard → **"New Project"**
2. **"Deploy from GitHub repo"** → `kommunal-monitoring` ni tanlang
3. **"Deploy Now"** ni bosing

### Qadam 3: PostgreSQL qo'shish
1. Project ichida **"+ New"** → **"Database"** → **"PostgreSQL"**
2. Avtomatik yaratiladi va `DATABASE_URL` ulanadi

### Qadam 4: Environment Variables qo'shish
Web service ga bosing → **"Variables"** tab:

| Key | Value |
|-----|-------|
| `DJANGO_SECRET_KEY` | (yuqorida yaratilgan kalit) |

### Qadam 5: Public domen yaratish
**Settings** → **Networking** → **"Generate Domain"**

Chiqqan domeni nusxalang, masalan: `kommunal-monitoring.up.railway.app`

### Qadam 6: `RAILWAY_PUBLIC_DOMAIN` qo'shish
**Variables** tabga qaytib qo'shing:

| Key | Value |
|-----|-------|
| `RAILWAY_PUBLIC_DOMAIN` | `kommunal-monitoring.up.railway.app` |

(`https://` siz!)

### Qadam 7: Qayta deploy
**"Deployments"** tabi → eng yuqori → **"Redeploy"**

✅ Tayyor: `https://kommunal-monitoring.up.railway.app`

### Yangilash
```bash
git add . && git commit -m "yangilash" && git push
```
Railway avtomatik deploy qiladi.

### ⚠️ Railway eslatma
- $5 kredit har oy beriladi (sizning loyihangiz uchun yetarli)
- Trial tugagach kredit karta majburiy

---

## 📊 Yakuniy taqqoslash

| Xususiyat | Render | Fly.io | Railway |
|-----------|--------|--------|---------|
| Karta kerakmi | ❌ Yo'q | ✅ Ha | ✅ Ha |
| Uxlaydimi | ⚠️ 15 daq. | ✅ Yo'q | ✅ Yo'q |
| Deploy usuli | GitHub auto | CLI (flyctl) | GitHub auto |
| Database | PostgreSQL bepul | SQLite + Volume | PostgreSQL bepul |
| Tezligi | O'rtacha | Eng tez | Tez |
| Eng oson | ⭐⭐⭐ | ⭐ | ⭐⭐ |

---

## 🐛 Tez-tez uchraydigan muammolar

### "Build failed" — Render

Logs da pastdan yuqoriga o'qing. Eng ko'p:

| Xato | Yechim |
|------|--------|
| `Permission denied: ./build.sh` | Linux/Mac da: `chmod +x build.sh && git add build.sh && git commit -m "fix" && git push` |
| `psycopg2 error` | `requirements.txt` da `psycopg2-binary` borligini tekshiring |
| `relation does not exist` | `build.sh` da `migrate` borligini tekshiring |

### "Application failed" — Fly.io

```bash
flyctl logs
```

Eng ko'p:
| Xato | Yechim |
|------|--------|
| Volume mount muammosi | `flyctl volumes list` ni tekshiring |
| Memory tugagan | `flyctl scale memory 512` |

### "502 Bad Gateway" — Railway

- **Variables** da `DJANGO_SECRET_KEY` borligini tekshiring
- **Settings** → **Logs** ni o'qing
- `RAILWAY_PUBLIC_DOMAIN` to'g'ri kiritilganmi?

### CSS/JS ishlamayapti (umumiy)

- `whitenoise` `MIDDLEWARE` ga avtomatik qo'shilgan
- `collectstatic` `build.sh` / `Dockerfile` da bor
- Brauzerda Ctrl+F5 (cache tozalash)

### Login ishlamayapti — CSRF xatolik

`settings.py` da `CSRF_TRUSTED_ORIGINS` to'g'ri sozlangan. Agar baribir ishlamasa:

```bash
# Render
# Environment Variables ga qo'shing:
# RENDER_EXTERNAL_HOSTNAME=kommunal-monitoring.onrender.com

# Railway
# RAILWAY_PUBLIC_DOMAIN=kommunal-monitoring.up.railway.app

# Fly.io
# (avtomatik FLY_APP_NAME orqali)
```

---

## 🎯 Tavsiyam

- 🥇 **Boshlanishiga:** **Render** — kartasiz, eng oson
- 🥈 **Production uchun:** **Fly.io** — uxlamaydi, tezroq
- 🥉 **Tez prototip:** **Railway** — eng tez setup

---

## 📱 Mock SMS muammosi (uchchalasi uchun ham)

Loyihada SMS kodi terminalga chiqadi. Production da foydalanuvchi ko'rmaydi.

### Yechim 1: Test foydalanuvchini reklama qilish
Login sahifasida tayyor: `+998901234567` / `parol12345`

### Yechim 2: Loglardan ko'rish (admin uchun)
- **Render:** Web Service → **"Logs"** tab
- **Fly.io:** `flyctl logs`
- **Railway:** Service → **"Deployments"** → **"View Logs"**

### Yechim 3: SMS kodni ekranda ko'rsatish (DEMO uchun)

`core/utils.py` faylida `send_mock_sms` funksiyasini topib:

```python
def send_mock_sms(phone, purpose='register'):
    code = f'{random.randint(100000, 999999)}'
    SmsCode.objects.create(phone=phone, code=code, purpose=purpose)
    print(f'📱 SMS kod {phone}: {code}')
    # DEMO uchun — foydalanuvchiga ko'rsatish
    # (production da o'chirib qo'ying!)
    return code
```

So'ng `views.py` da `register_phone` funksiyasiga qo'shing (`send_mock_sms` chaqirilgan joydan keyin):

```python
messages.info(request, f'📱 [DEMO rejim] Tasdiqlash kodi: {code}')
```

---

## ✅ Yakuniy tekshiruv ro'yxati

Deploy qilishdan oldin:

- [x] `requirements.txt` da gunicorn, whitenoise, dj-database-url, psycopg2-binary bor
- [x] `config/settings.py` ning oxirida UNIVERSAL PRODUCTION bloki bor
- [x] `build.sh` yaratilgan
- [x] `Dockerfile` va `.dockerignore` yaratilgan
- [x] `fly.toml`, `railway.json`, `Procfile`, `runtime.txt` yaratilgan
- [x] `seed_data.py` xavfsiz holatda (qaytadan ishlamaydi)
- [x] `.gitignore` to'g'ri
- [ ] Kod GitHub'ga push qilingan ← buni o'zingiz qilasiz
- [ ] `DJANGO_SECRET_KEY` yaratilgan ← buni o'zingiz yaratasiz
- [ ] Variables platformaga kiritilgan ← deploy paytida

Hammasi tayyor bo'lsa — har 3 servisga ham 10-15 daqiqada deploy qilasiz! 🚀
