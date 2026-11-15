from sqlmodel import Session, SQLModel, create_engine  # นำเข้าเครื่องมือเชื่อมต่อฐานข้อมูลจาก SQLModel

from app.config import settings  # นำเข้าค่าตั้งค่า เพื่ออ่าน database_url

database_url = settings.database_url  # อ่านที่อยู่ฐานข้อมูลจาก .env หรือใช้ค่าเริ่มต้น SQLite

# Render ให้ที่อยู่แบบ postgresql:// แต่ SQLModel ต้องรู้ว่าใช้ driver ตัวไหน จึงเติม +psycopg เข้าไป
if database_url.startswith("postgresql://"):  # ตรวจว่าเป็นที่อยู่ของ Postgres ที่ยังไม่ได้ระบุ driver หรือไม่
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)  # เปลี่ยนให้ใช้ driver psycopg (เวอร์ชัน 3)

connect_args = {}  # ตัวเลือกเพิ่มเติมตอนเชื่อมต่อ เริ่มจากว่างไว้ก่อน
if database_url.startswith("sqlite"):  # SQLite มีข้อจำกัดเรื่องการใช้จากหลาย thread
    connect_args = {"check_same_thread": False}  # อนุญาตให้ FastAPI ใช้การเชื่อมต่อเดียวกันจากหลาย thread ได้

engine = create_engine(database_url, connect_args=connect_args)  # สร้างตัวเชื่อมต่อฐานข้อมูลไว้ครั้งเดียวทั้งแอป


def create_db_and_tables():  # ฟังก์ชันสร้างตารางทุกตารางที่ประกาศไว้ใน models.py
    SQLModel.metadata.create_all(engine)  # สร้างเฉพาะตารางที่ยังไม่มี ตารางที่มีอยู่แล้วจะไม่ถูกลบ


def get_session():  # dependency ที่ให้ session ฐานข้อมูลกับฟังก์ชันของ endpoint
    with Session(engine) as session:  # เปิด session ใหม่ทุกครั้งที่มี request เข้ามา
        yield session  # ส่ง session ให้ฟังก์ชันของ endpoint ใช้ เมื่อทำงานเสร็จ with จะปิด session ให้เอง
