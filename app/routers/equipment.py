from fastapi import APIRouter, HTTPException, status  # นำเข้าเครื่องมือสร้างกลุ่ม endpoint และการตอบ error
from sqlmodel import select  # นำเข้า select สำหรับค้นหาข้อมูลในฐานข้อมูล

from app.models import Equipment, EquipmentCreate, EquipmentPublic, Loan  # นำเข้าตารางและรูปแบบข้อมูลที่ใช้ในไฟล์นี้
from app.security import SessionDep, StaffUser  # นำเข้า dependency ของ session ฐานข้อมูลและผู้ใช้ staff

router = APIRouter(prefix="/equipment", tags=["equipment"])  # กลุ่ม endpoint ที่ขึ้นต้นด้วย /equipment


def get_equipment_or_404(session: SessionDep, equipment_id: int) -> Equipment:  # ค้นหาอุปกรณ์ ถ้าไม่พบให้ตอบ 404
    equipment = session.get(Equipment, equipment_id)  # ค้นหาด้วย primary key ได้ None ถ้าไม่พบ
    if equipment is None:  # ไม่พบอุปกรณ์รหัสนี้
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบอุปกรณ์")  # ตอบ 404 Not Found
    return equipment  # คืนอุปกรณ์ที่พบ


def ensure_serial_unique(session: SessionDep, serial_no: str, equipment_id: int | None = None):  # ตรวจว่าเลขครุภัณฑ์ไม่ซ้ำ
    statement = select(Equipment).where(Equipment.serial_no == serial_no)  # คำสั่งค้นหาอุปกรณ์ที่มีเลขครุภัณฑ์นี้
    existing = session.exec(statement).first()  # รันคำสั่งแล้วเอาแถวแรก ได้ None ถ้าไม่มี
    if existing is not None and existing.id != equipment_id:  # มีอยู่แล้ว และไม่ใช่อุปกรณ์ชิ้นที่กำลังแก้ไข
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="เลขครุภัณฑ์นี้มีอยู่แล้ว")  # ตอบ 409 Conflict


@router.get("", response_model=list[EquipmentPublic])  # GET /equipment ดูอุปกรณ์ทั้งหมด
def list_equipment(session: SessionDep, category: str | None = None):  # category เป็น query parameter ไม่ใส่ก็ได้
    statement = select(Equipment)  # เริ่มจากคำสั่งเลือกอุปกรณ์ทุกชิ้น
    if category:  # ถ้าผู้ใช้ส่ง ?category= มา
        statement = statement.where(Equipment.category == category)  # กรองเฉพาะหมวดหมู่ที่ระบุ
    return session.exec(statement.order_by(Equipment.id)).all()  # เรียงตามรหัส แล้วคืนเป็น list


@router.get("/{equipment_id}", response_model=EquipmentPublic)  # GET /equipment/{equipment_id} ดูอุปกรณ์ 1 ชิ้น
def read_equipment(equipment_id: int, session: SessionDep):  # equipment_id เป็น path parameter ชนิด int
    return get_equipment_or_404(session, equipment_id)  # คืนอุปกรณ์ หรือตอบ 404 ถ้าไม่พบ


@router.post("", response_model=EquipmentPublic, status_code=status.HTTP_201_CREATED)  # POST /equipment เพิ่มอุปกรณ์ ตอบ 201
def create_equipment(data: EquipmentCreate, session: SessionDep, staff: StaffUser):  # staff: ต้อง login เป็น staff
    ensure_serial_unique(session, data.serial_no)  # ตรวจเลขครุภัณฑ์ซ้ำก่อนบันทึก
    equipment = Equipment(**data.model_dump())  # แปลงข้อมูลที่ตรวจแล้วเป็น dict แล้วสร้างแถวใหม่ของตาราง Equipment
    session.add(equipment)  # เตรียมบันทึกแถวใหม่
    session.commit()  # บันทึกลงฐานข้อมูลจริง
    session.refresh(equipment)  # อ่านค่าล่าสุดกลับมา เพื่อให้ได้ id ที่ฐานข้อมูลสร้างให้
    return equipment  # ส่งอุปกรณ์ที่เพิ่มแล้วกลับไป


@router.put("/{equipment_id}", response_model=EquipmentPublic)  # PUT /equipment/{equipment_id} แก้ไขอุปกรณ์
def update_equipment(equipment_id: int, data: EquipmentCreate, session: SessionDep, staff: StaffUser):  # ต้องเป็น staff
    equipment = get_equipment_or_404(session, equipment_id)  # หาอุปกรณ์ที่จะแก้ ถ้าไม่พบตอบ 404
    ensure_serial_unique(session, data.serial_no, equipment_id)  # เลขครุภัณฑ์ใหม่ต้องไม่ซ้ำกับชิ้นอื่น
    equipment.sqlmodel_update(data.model_dump())  # นำค่าใหม่ทุกฟิลด์ไปแทนค่าเดิม
    session.add(equipment)  # เตรียมบันทึกการเปลี่ยนแปลง
    session.commit()  # บันทึกลงฐานข้อมูลจริง
    session.refresh(equipment)  # อ่านค่าล่าสุดกลับมา
    return equipment  # ส่งอุปกรณ์ที่แก้แล้วกลับไป


@router.delete("/{equipment_id}", status_code=status.HTTP_204_NO_CONTENT)  # DELETE ลบอุปกรณ์ ตอบ 204 ไม่มีเนื้อหา
def delete_equipment(equipment_id: int, session: SessionDep, staff: StaffUser):  # ต้องเป็น staff
    equipment = get_equipment_or_404(session, equipment_id)  # หาอุปกรณ์ที่จะลบ ถ้าไม่พบตอบ 404
    has_loans = session.exec(select(Loan).where(Loan.equipment_id == equipment_id)).first()  # มีประวัติการยืมหรือไม่
    if has_loans is not None:  # ถ้าเคยถูกยืม การลบจะทำให้ประวัติการยืมชี้ไปที่อุปกรณ์ที่ไม่มีอยู่
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="อุปกรณ์นี้มีประวัติการยืม ลบไม่ได้")  # ตอบ 409
    session.delete(equipment)  # เตรียมลบแถวนี้
    session.commit()  # ลบออกจากฐานข้อมูลจริง
