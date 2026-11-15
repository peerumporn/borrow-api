from contextlib import asynccontextmanager  # นำเข้าเครื่องมือสร้างฟังก์ชันที่ทำงานตอนแอปเริ่มและตอนปิด
from pathlib import Path  # นำเข้า Path ใช้หาตำแหน่งโฟลเดอร์ static

from fastapi import FastAPI  # นำเข้าคลาส FastAPI ที่ใช้สร้างเว็บแอป
from fastapi.staticfiles import StaticFiles  # นำเข้าเครื่องมือเสิร์ฟไฟล์ HTML สำหรับบทเสริม
from sqlmodel import Session, select  # นำเข้า Session และ select สำหรับสร้าง staff คนแรก

from app.config import settings  # นำเข้าค่าตั้งค่า เพื่ออ่านชื่อและรหัสผ่านของ staff คนแรก
from app.database import create_db_and_tables, engine  # นำเข้าฟังก์ชันสร้างตารางและตัวเชื่อมต่อฐานข้อมูล
from app.models import User  # นำเข้าตาราง User
from app.routers import auth, equipment, loans  # นำเข้ากลุ่ม endpoint ทั้ง 3 ไฟล์
from app.security import hash_password  # นำเข้าฟังก์ชัน hash รหัสผ่าน


def check_production_settings():  # กันไม่ให้ขึ้น cloud ด้วยค่าตัวอย่างที่ใครอ่านเล่มก็รู้
    on_cloud = settings.database_url.startswith("postgres")  # ใช้ Postgres แปลว่ากำลังรันบน Render ไม่ใช่เครื่องตัวเอง
    uses_example = "change-me" in settings.secret_key or "change-me" in settings.staff_password  # ยังใช้ค่าปลอมจาก .env.example อยู่หรือไม่
    if on_cloud and uses_example:  # ถ้าขึ้น cloud แล้วแต่ยังใช้ค่าปลอม
        raise RuntimeError("ตั้ง SECRET_KEY และ STAFF_PASSWORD ใน Environment ของ Render ก่อน")  # หยุดแอปและเขียนสาเหตุไว้ใน log


def create_first_staff():  # สร้างผู้ใช้ staff คนแรกจากค่าใน .env ถ้ายังไม่มี
    with Session(engine) as session:  # เปิด session ฐานข้อมูลชั่วคราว
        statement = select(User).where(User.username == settings.staff_username)  # คำสั่งค้นหา staff ตามชื่อใน .env
        if session.exec(statement).first() is None:  # ถ้ายังไม่มีผู้ใช้ชื่อนี้
            staff = User(  # สร้างผู้ใช้ staff
                username=settings.staff_username,  # ชื่อผู้ใช้จาก .env
                full_name="ผู้ดูแลระบบ",  # ชื่อแสดงของ staff คนแรก
                hashed_password=hash_password(settings.staff_password),  # hash รหัสผ่านจาก .env
                role="staff",  # กำหนดบทบาทเป็น staff
            )
            session.add(staff)  # เตรียมบันทึก
            session.commit()  # บันทึกลงฐานข้อมูลจริง


@asynccontextmanager  # ทำให้ฟังก์ชันข้างล่างใช้เป็น lifespan ได้
async def lifespan(app: FastAPI):  # โค้ดก่อน yield ทำงานตอนเริ่มแอป โค้ดหลัง yield ทำงานตอนปิดแอป
    check_production_settings()  # ตรวจค่าลับก่อนเริ่มทำงานจริง
    create_db_and_tables()  # สร้างตารางที่ยังไม่มี
    create_first_staff()  # สร้าง staff คนแรก
    yield  # ให้แอปเริ่มรับ request ได้


app = FastAPI(title="Borrow API", description="ระบบยืม-คืนอุปกรณ์แผนกวิชา", lifespan=lifespan)  # สร้างแอปของเรา

app.include_router(auth.router)  # เพิ่มกลุ่ม endpoint /auth
app.include_router(equipment.router)  # เพิ่มกลุ่ม endpoint /equipment
app.include_router(loans.router)  # เพิ่มกลุ่ม endpoint /loans

static_dir = Path(__file__).parent / "static"  # หาตำแหน่งโฟลเดอร์ app/static จากตำแหน่งของไฟล์นี้
app.mount("/static", StaticFiles(directory=static_dir, html=True), name="static")  # เสิร์ฟหน้าเว็บที่ /static/


@app.get("/")  # GET / ทดสอบว่าเซิร์ฟเวอร์ทำงาน
def read_root():  # ฟังก์ชันที่ทำงานเมื่อมีคนเข้าหน้าแรก
    return {"message": "สวัสดี Borrow API"}  # FastAPI แปลง dict เป็น JSON ให้อัตโนมัติ


@app.get("/health")  # GET /health ให้ Render ใช้ตรวจว่าแอปยังทำงานอยู่
def health_check():  # ฟังก์ชันตรวจสุขภาพแบบง่าย
    return {"status": "ok"}  # ตอบ 200 พร้อมสถานะ ok
