# Borrow API — ระบบยืม-คืนอุปกรณ์แผนกวิชา

โค้ดอ้างอิงฉบับสมบูรณ์ (ภาคผนวก ค) ของเอกสารอบรม "การพัฒนาเว็บ API ด้วย FastAPI และการ Deploy บน Cloud"

สร้างและรันด้วย uv ทดสอบแล้วกับ Python 3.12, SQLite (เครื่องตัวเอง) และ PostgreSQL 16 (จำลอง Render)

---

## ส่วนที่ 1 รันบนเครื่องตัวเอง (ด้วย uv)

โปรเจกต์นี้ใช้ [uv](https://docs.astral.sh/uv/) จัดการ Python, virtual environment และ package ในคำสั่งเดียว
รายชื่อ package อยู่ใน `pyproject.toml` และเวอร์ชันที่ทดสอบแล้วถูกล็อกไว้ใน `uv.lock` (ต้อง commit ทั้งสองไฟล์)

> ⚠️ ถ้าโฟลเดอร์นี้อยู่ใน Google Drive, OneDrive หรือ Dropbox ให้คัดลอกออกมาไว้ที่อื่นก่อน เช่น `C:\dev\borrow-api`
> เพราะ `.venv` มีไฟล์หลายพันไฟล์ โปรแกรม sync จะทำงานหนักและอาจทำให้ไฟล์เสีย

### 1.1 ติดตั้ง uv (ครั้งเดียวต่อเครื่อง)

<!-- TODO: ตรวจสอบกับเอกสารทางการ — คำสั่งติดตั้ง uv ล่าสุดจาก docs.astral.sh/uv -->

**Windows (PowerShell)**
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux**
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

ปิดแล้วเปิด terminal ใหม่ แล้วตรวจด้วย `uv --version` (ถ้าติดตั้งแบบข้างบนไม่ได้ ใช้ `pip install uv` แทนได้)

### 1.2 เตรียมโปรเจกต์

```bash
cd C:\dev\borrow-api      # macOS/Linux: cd ~/dev/borrow-api
uv sync                    # สร้าง .venv และติดตั้ง package ตาม uv.lock (ถ้าเครื่องไม่มี Python 3.12 uv จะดาวน์โหลดให้)
copy .env.example .env     # macOS/Linux: cp .env.example .env
```

ไม่ต้องสร้างหรือ activate virtual environment เอง เพราะ `uv run` จัดการให้ทุกครั้ง

### 1.3 รันเซิร์ฟเวอร์

```bash
uv run fastapi dev app/main.py
```

| เปิดในเบราว์เซอร์ | ใช้ทำอะไร |
|---|---|
| http://127.0.0.1:8000/docs | ทดลองเรียกทุก endpoint (Swagger UI) |
| http://127.0.0.1:8000/static/ | หน้าเว็บ login ยืม และคืนอุปกรณ์ |
| http://127.0.0.1:8000/health | ตรวจว่าเซิร์ฟเวอร์ทำงาน |

ผู้ใช้ staff คนแรกสร้างให้อัตโนมัติจาก `.env` คือ `admin` / `change-me-in-env`

### 1.4 ใส่ข้อมูลตัวอย่าง

ฐานข้อมูลเริ่มต้นว่าง ให้ login เป็น staff แล้วเพิ่มอุปกรณ์ จะทำผ่าน `/docs` (ปุ่ม **Authorize**) หรือใช้ `curl` ก็ได้

คำสั่ง `curl` ข้างล่างใช้กับ Git Bash, macOS หรือ Linux ส่วนบน Windows ที่ใช้ PowerShell แนะนำให้ทำผ่าน `/docs`

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/auth/login -d "username=admin&password=change-me-in-env" | uv run python -c "import sys,json;print(json.load(sys.stdin)['access_token'])")
curl -X POST http://127.0.0.1:8000/equipment -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"name":"Arduino Uno","category":"microcontroller","serial_no":"ARD-001"}'
```

ส่วนผู้ใช้ `student` ให้สมัครเองผ่าน `POST /auth/register`

### 1.5 เริ่มฐานข้อมูลใหม่

หยุดเซิร์ฟเวอร์ (Ctrl+C) แล้วลบไฟล์ `borrow.db` จากนั้นรัน `uv run fastapi dev app/main.py` อีกครั้ง

### 1.6 คำสั่ง uv ที่ใช้บ่อย

| คำสั่ง | ใช้ทำอะไร |
|---|---|
| `uv run <คำสั่ง>` | รันคำสั่งใน virtual environment ของโปรเจกต์ เช่น `uv run fastapi dev app/main.py` |
| `uv add <package>` | เพิ่ม package ลงใน `pyproject.toml` และ `uv.lock` แล้วติดตั้งให้ |
| `uv remove <package>` | ลบ package |
| `uv sync` | ติดตั้ง package ให้ตรงกับ `uv.lock` (ใช้หลัง clone หรือ pull) |

### 1.7 วิธีสร้างโปรเจกต์นี้ตั้งแต่ศูนย์

```bash
uv init --app --bare --name borrow-api --python 3.12
uv python pin 3.12
uv add "fastapi[standard]" sqlmodel pydantic-settings "pwdlib[argon2]" pyjwt "psycopg[binary]"
```

จากนั้นสร้างโฟลเดอร์ `app/` ตามโครงสร้างท้าย README นี้

---

## ส่วนที่ 2 ส่งขึ้น GitHub

```bash
git init
git add .
git commit -m "Borrow API"
git branch -M main
git remote add origin https://github.com/<ชื่อบัญชี>/borrow-api.git
git push -u origin main
```

> ⛔ ก่อน push ให้รัน `git status` แล้วตรวจว่า **ไม่มี** `.env`, `.venv/` และ `borrow.db` อยู่ในรายการ ทั้ง 3 อย่างอยู่ใน `.gitignore` แล้ว
> แต่ **ต้องมี** `pyproject.toml`, `uv.lock` และ `.python-version` เพราะ Render ใช้ 3 ไฟล์นี้ติดตั้ง package

---

## ส่วนที่ 3 Deploy ขึ้น Render

<!-- TODO: ตรวจสอบกับเอกสารทางการ — ชื่อเมนู ปุ่ม และเงื่อนไขแผนฟรีของ Render ณ วันที่สอน -->

### 3.1 สร้างฐานข้อมูล Postgres

1. ใน Render Dashboard เลือก **New → Postgres**
2. ตั้งชื่อ เช่น `borrow-db` เลือก Region ที่ใกล้ที่สุด (เช่น Singapore) และเลือกแผน **Free**
3. เมื่อสร้างเสร็จ ให้คัดลอก **Internal Database URL** เก็บไว้

### 3.2 สร้าง Web Service

1. เลือก **New → Web Service** แล้วเชื่อมกับ repository `borrow-api` บน GitHub
2. ตั้งค่าตามตารางนี้

| ช่อง | ค่า |
|---|---|
| Language | Python 3 |
| Region | **Region เดียวกับฐานข้อมูล** (ถ้าคนละ Region จะใช้ Internal Database URL ไม่ได้) |
| Branch | `main` |
| Build Command | `pip install uv && uv sync --frozen` |
| Start Command | `.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Instance Type | Free |
| Health Check Path | `/health` (อยู่ในส่วน Advanced) |

3. เพิ่ม **Environment Variables** ครบทั้ง 4 ตัว

| Key | Value |
|---|---|
| `DATABASE_URL` | Internal Database URL จากข้อ 3.1 (ขึ้นต้นด้วย `postgresql://` ใช้ได้เลย โค้ดแปลงให้เอง) |
| `SECRET_KEY` | ค่าสุ่มยาว 64 ตัว สร้างด้วย `python -c "import secrets; print(secrets.token_hex(32))"` |
| `STAFF_USERNAME` | ชื่อผู้ใช้ staff เช่น `admin` |
| `STAFF_PASSWORD` | รหัสผ่าน staff ที่เดายาก **ห้ามใช้ค่าจาก `.env.example`** |

4. กด **Create Web Service** แล้วรอจนสถานะเป็น **Live**

> ⛔ ถ้าลืมตั้ง `SECRET_KEY` หรือ `STAFF_PASSWORD` หรือยังใช้ค่า `change-me-...` อยู่ แอปจะไม่ยอมเริ่มทำงาน
> ในหน้า **Logs** จะเห็น `RuntimeError: ตั้ง SECRET_KEY และ STAFF_PASSWORD ใน Environment ของ Render ก่อน`
> ระบบตั้งใจให้เป็นแบบนี้ เพื่อกันไม่ให้ระบบบน cloud ใช้รหัสผ่านที่ใครอ่านเล่มก็รู้

> 💡 ทำไม Build และ Start Command หน้าตาแบบนี้
> - `uv sync --frozen` ติดตั้ง package ตาม `uv.lock` เป๊ะ ๆ ถ้า `pyproject.toml` กับ `uv.lock` ไม่ตรงกัน build จะล้ม (กันไม่ให้ได้เวอร์ชันที่ไม่เคยทดสอบ)
> - uv ใช้ Python ตาม `.python-version` (3.12) ถ้าเครื่องของ Render ไม่มี uv จะดาวน์โหลดให้ระหว่าง build
> - Start Command เรียก `uvicorn` จาก `.venv` ที่สร้างตอน build โดยตรง จึงไม่ต้องพึ่ง uv ตอนรันจริง
> <!-- TODO: ตรวจสอบกับเอกสารทางการ — Render อาจรองรับ uv โดยตรงแล้ว ถ้าใช่ Build Command อาจเหลือแค่ `uv sync --frozen` -->

### 3.3 ตรวจว่า deploy สำเร็จ

แทน `<ชื่อแอป>` ด้วย URL ที่ Render ให้มา

```bash
curl https://<ชื่อแอป>.onrender.com/health
```

ต้องได้ `{"status":"ok"}` จากนั้นเปิด `https://<ชื่อแอป>.onrender.com/static/` ในมือถือ แล้วลอง login, ยืม และคืนอุปกรณ์

> 💡 Web Service แผนฟรีจะหลับเมื่อไม่มีคนใช้สักพัก request แรกหลังหลับอาจใช้เวลาประมาณ 1 นาที (cold start) ช่วงนั้นถือว่าปกติ

### 3.4 อัปเดตโค้ดหลัง deploy

แก้โค้ดในเครื่อง แล้วรัน `git add .` → `git commit -m "..."` → `git push` จากนั้น Render จะ build และ deploy ให้ใหม่เอง

---

## Endpoint และสิทธิ์การใช้งาน

| Method | Path | ใครใช้ได้ |
|---|---|---|
| GET | `/`, `/health` | ทุกคน |
| GET | `/equipment`, `/equipment/{equipment_id}` | ทุกคน (กรองหมวดหมู่ด้วย `?category=`) |
| POST | `/auth/register` | ทุกคน (สมัครเองได้ role `student` เสมอ) |
| POST | `/auth/login` | ทุกคน (ส่งแบบฟอร์ม `username` + `password`) |
| GET | `/auth/me` | ผู้ใช้ที่ login แล้ว |
| POST / GET | `/loans` | ผู้ใช้ที่ login แล้ว (student เห็นเฉพาะรายการของตัวเอง) |
| POST | `/loans/{loan_id}/return` | ผู้ยืมเอง หรือ staff |
| POST / PUT / DELETE | `/equipment...` | staff เท่านั้น |

## ค่าใน `.env`

| ตัวแปร | ความหมาย |
|---|---|
| `DATABASE_URL` | ไม่ตั้ง หรือ `sqlite:///./borrow.db` = SQLite ในเครื่อง / บน Render ใช้ Internal Database URL |
| `SECRET_KEY` | กุญแจเซ็น JWT ยาวอย่างน้อย 32 ตัวอักษร |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | อายุ JWT เป็นนาที (ค่าเริ่มต้น 30) |
| `STAFF_USERNAME`, `STAFF_PASSWORD` | staff คนแรกที่ระบบสร้างให้ตอนเริ่มทำงาน |

## โครงสร้างไฟล์

```text
borrow-api/
├── app/
│   ├── __init__.py
│   ├── main.py          # จุดเริ่มต้นของแอป ตรวจค่าลับ สร้างตาราง และ staff คนแรก
│   ├── config.py        # อ่านค่าจาก .env
│   ├── database.py      # เชื่อมต่อฐานข้อมูล (SQLite หรือ Postgres)
│   ├── models.py        # ตาราง (SQLModel) และข้อมูลขาเข้า/ขาออก (Pydantic)
│   ├── security.py      # hash รหัสผ่าน, JWT และการตรวจสิทธิ์
│   ├── routers/
│   │   ├── equipment.py
│   │   ├── loans.py
│   │   └── auth.py
│   └── static/
│       └── index.html   # หน้าเว็บ Alpine.js + Tailwind
├── .env.example         # แม่แบบของ .env (commit ได้)
├── .gitignore
├── .python-version      # Python 3.12 (uv ใช้ไฟล์นี้)
├── pyproject.toml       # รายชื่อ package
├── uv.lock              # เวอร์ชัน package ที่ทดสอบแล้ว (ต้อง commit)
└── README.md
```
