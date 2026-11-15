from fastapi import APIRouter, HTTPException, status  # นำเข้าเครื่องมือสร้างกลุ่ม endpoint และการตอบ error
from sqlmodel import select  # นำเข้า select สำหรับค้นหาข้อมูลในฐานข้อมูล

from app.models import Equipment, Loan, LoanCreate, LoanPublic, utc_now  # นำเข้าตาราง รูปแบบข้อมูล และฟังก์ชันเวลาปัจจุบัน
from app.security import CurrentUser, SessionDep  # นำเข้า dependency ของผู้ใช้ที่ login และ session ฐานข้อมูล

router = APIRouter(prefix="/loans", tags=["loans"])  # กลุ่ม endpoint ที่ขึ้นต้นด้วย /loans


@router.post("", response_model=LoanPublic, status_code=status.HTTP_201_CREATED)  # POST /loans ยืมอุปกรณ์ ตอบ 201
def borrow_equipment(data: LoanCreate, session: SessionDep, user: CurrentUser):  # ต้อง login ผู้ยืมคือผู้ใช้คนนี้
    equipment = session.get(Equipment, data.equipment_id)  # หาอุปกรณ์ที่ต้องการยืม
    if equipment is None:  # ไม่พบอุปกรณ์รหัสนี้
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบอุปกรณ์")  # ตอบ 404
    if not equipment.is_available:  # กฎธุรกิจข้อ 1: อุปกรณ์ถูกยืมอยู่แล้ว
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="อุปกรณ์นี้ถูกยืมอยู่")  # ตอบ 409 Conflict
    loan = Loan(user_id=user.id, equipment_id=equipment.id)  # สร้างรายการยืมใหม่ เวลายืมใส่ให้อัตโนมัติ
    equipment.is_available = False  # เปลี่ยนสถานะอุปกรณ์เป็นไม่ว่าง
    session.add(loan)  # เตรียมบันทึกรายการยืม
    session.add(equipment)  # เตรียมบันทึกสถานะอุปกรณ์
    session.commit()  # บันทึกทั้งสองอย่างพร้อมกัน สำเร็จทั้งคู่หรือไม่บันทึกเลย
    session.refresh(loan)  # อ่านค่าล่าสุดกลับมา เพื่อให้ได้ id ของรายการยืม
    return loan  # ส่งรายการยืมกลับไป


@router.post("/{loan_id}/return", response_model=LoanPublic)  # POST /loans/{loan_id}/return คืนอุปกรณ์
def return_equipment(loan_id: int, session: SessionDep, user: CurrentUser):  # ต้อง login
    loan = session.get(Loan, loan_id)  # หารายการยืมที่จะคืน
    if loan is None:  # ไม่พบรายการยืมรหัสนี้
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="ไม่พบรายการยืม")  # ตอบ 404
    if loan.user_id != user.id and user.role != "staff":  # คืนได้เฉพาะผู้ยืมเอง หรือ staff
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="คืนได้เฉพาะผู้ยืมหรือ staff")  # ตอบ 403
    if loan.returned_at is not None:  # รายการนี้คืนไปแล้ว
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="รายการนี้คืนแล้ว")  # ตอบ 409
    equipment = session.get(Equipment, loan.equipment_id)  # หาอุปกรณ์ของรายการยืมนี้
    loan.returned_at = utc_now()  # กฎธุรกิจข้อ 2: บันทึกเวลาคืน
    equipment.is_available = True  # กฎธุรกิจข้อ 2: อุปกรณ์กลับมาว่าง
    session.add(loan)  # เตรียมบันทึกรายการยืม
    session.add(equipment)  # เตรียมบันทึกสถานะอุปกรณ์
    session.commit()  # บันทึกทั้งสองอย่างพร้อมกัน
    session.refresh(loan)  # อ่านค่าล่าสุดกลับมา
    return loan  # ส่งรายการยืมที่คืนแล้วกลับไป


@router.get("", response_model=list[LoanPublic])  # GET /loans ดูรายการยืม
def list_loans(session: SessionDep, user: CurrentUser):  # ต้อง login
    statement = select(Loan)  # เริ่มจากคำสั่งเลือกรายการยืมทั้งหมด
    if user.role != "staff":  # student เห็นเฉพาะรายการของตัวเอง
        statement = statement.where(Loan.user_id == user.id)  # กรองเฉพาะรายการที่ผู้ใช้คนนี้ยืม
    return session.exec(statement.order_by(Loan.id)).all()  # เรียงตามรหัส แล้วคืนเป็น list
