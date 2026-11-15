from datetime import datetime, timezone  # นำเข้าเครื่องมือจัดการวันเวลา ใช้บันทึกเวลายืมและคืน
from typing import Literal  # นำเข้า Literal เพื่อจำกัดให้ค่า role มีได้แค่บางค่า

from pydantic import BaseModel, ConfigDict, Field  # นำเข้า Pydantic สำหรับตรวจสอบข้อมูลขาเข้าและกำหนดรูปแบบข้อมูลขาออก
from sqlmodel import Field as DBField  # นำเข้า Field ของ SQLModel ตั้งชื่อใหม่ไม่ให้ปนกับของ Pydantic
from sqlmodel import SQLModel  # นำเข้า SQLModel สำหรับประกาศตารางในฐานข้อมูล


def utc_now():  # ฟังก์ชันคืนเวลาปัจจุบันแบบ UTC ใช้เป็นค่าเริ่มต้นของ borrowed_at
    return datetime.now(timezone.utc)  # ใช้ UTC เพื่อให้เวลาตรงกันไม่ว่าเซิร์ฟเวอร์จะอยู่ประเทศไหน


# ---------- ตารางในฐานข้อมูล (SQLModel, table=True) ----------

class User(SQLModel, table=True):  # ตาราง User ในฐานข้อมูล
    id: int | None = DBField(default=None, primary_key=True)  # รหัสผู้ใช้ ฐานข้อมูลสร้างเลขให้อัตโนมัติ
    username: str = DBField(unique=True, index=True)  # ชื่อผู้ใช้ ห้ามซ้ำ และทำ index ให้ค้นหาเร็ว
    full_name: str  # ชื่อ-นามสกุลจริง
    hashed_password: str  # รหัสผ่านที่ hash แล้ว ห้ามเก็บรหัสผ่านจริงเด็ดขาด
    role: str = "student"  # บทบาทของผู้ใช้ มีได้ 2 ค่าคือ student และ staff


class Equipment(SQLModel, table=True):  # ตาราง Equipment ในฐานข้อมูล
    id: int | None = DBField(default=None, primary_key=True)  # รหัสอุปกรณ์ ฐานข้อมูลสร้างให้อัตโนมัติ
    name: str  # ชื่ออุปกรณ์
    category: str = DBField(index=True)  # หมวดหมู่ ทำ index เพราะใช้กรองบ่อย
    serial_no: str = DBField(unique=True)  # เลขครุภัณฑ์ ห้ามซ้ำ
    is_available: bool = True  # อุปกรณ์ใหม่ว่างเสมอ เปลี่ยนเป็น False เมื่อถูกยืม


class Loan(SQLModel, table=True):  # ตาราง Loan บันทึกการยืมแต่ละครั้ง
    id: int | None = DBField(default=None, primary_key=True)  # รหัสการยืม
    user_id: int = DBField(foreign_key="user.id")  # ผู้ยืม ชี้ไปที่ตาราง user
    equipment_id: int = DBField(foreign_key="equipment.id")  # อุปกรณ์ที่ยืม ชี้ไปที่ตาราง equipment
    borrowed_at: datetime = DBField(default_factory=utc_now)  # เวลายืม ระบบใส่ให้อัตโนมัติ
    returned_at: datetime | None = None  # เวลาคืน ว่างไว้ (None) ถ้ายังไม่คืน


# ---------- ข้อมูลขาเข้าและขาออก (Pydantic) ----------

class EquipmentCreate(BaseModel):  # ข้อมูลที่ต้องส่งมาตอนเพิ่มหรือแก้ไขอุปกรณ์
    name: str = Field(min_length=1, max_length=100)  # ชื่ออุปกรณ์ ห้ามว่าง และยาวไม่เกิน 100 ตัว
    category: str = Field(min_length=1, max_length=50)  # หมวดหมู่ ห้ามว่าง
    serial_no: str = Field(pattern=r"^[A-Z]{2,5}-\d{3,}$")  # เลขครุภัณฑ์รูปแบบ ABC-001 (อักษรใหญ่ 2–5 ตัว ขีด ตัวเลข 3 ตัวขึ้นไป)


class EquipmentPublic(BaseModel):  # ข้อมูลอุปกรณ์ที่ส่งกลับไป กำหนดลำดับฟิลด์ให้อ่านง่าย
    model_config = ConfigDict(from_attributes=True)  # อนุญาตให้อ่านค่าจากแถวของตาราง (อ็อบเจกต์) ไม่ใช่เฉพาะ dict

    id: int  # รหัสอุปกรณ์
    name: str  # ชื่ออุปกรณ์
    category: str  # หมวดหมู่
    serial_no: str  # เลขครุภัณฑ์
    is_available: bool  # ว่างหรือไม่


class LoanCreate(BaseModel):  # ข้อมูลที่ต้องส่งมาตอนยืม (ผู้ยืมได้จาก JWT ไม่ต้องส่งมา)
    equipment_id: int = Field(gt=0)  # รหัสอุปกรณ์ต้องเป็นเลขบวก


class LoanPublic(BaseModel):  # ข้อมูลการยืมที่ส่งกลับไป
    model_config = ConfigDict(from_attributes=True)  # อนุญาตให้อ่านค่าจากแถวของตาราง

    id: int  # รหัสการยืม
    user_id: int  # ผู้ยืม
    equipment_id: int  # อุปกรณ์ที่ยืม
    borrowed_at: datetime  # เวลายืม
    returned_at: datetime | None  # เวลาคืน เป็น null ถ้ายังไม่คืน


class UserCreate(BaseModel):  # ข้อมูลที่ผู้ใช้ส่งมาตอนสมัคร
    username: str = Field(min_length=3, max_length=20, pattern=r"^[a-z0-9_]+$")  # ตัวพิมพ์เล็ก ตัวเลข หรือ _ ยาว 3–20 ตัว
    full_name: str = Field(min_length=1, max_length=100)  # ชื่อจริง ห้ามว่าง และยาวไม่เกิน 100 ตัว
    password: str = Field(min_length=8, max_length=128)  # รหัสผ่าน 8–128 ตัว สั้นเกินไปจะเดาง่าย


class UserPublic(BaseModel):  # ข้อมูลผู้ใช้ที่ส่งกลับไปได้ (ไม่มี hashed_password)
    model_config = ConfigDict(from_attributes=True)  # อนุญาตให้อ่านค่าจากแถวของตาราง

    id: int  # รหัสผู้ใช้
    username: str  # ชื่อผู้ใช้
    full_name: str  # ชื่อจริง
    role: Literal["student", "staff"]  # บทบาท


class Token(BaseModel):  # รูปแบบข้อมูลที่ส่งกลับหลัง login สำเร็จ
    access_token: str  # ตัว JWT ที่ผู้ใช้ต้องแนบไปกับ request ต่อ ๆ ไป
    token_type: str = "bearer"  # ชนิดของ token บอก client ว่าต้องแนบแบบ Bearer
