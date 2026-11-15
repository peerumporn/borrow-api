from typing import Annotated  # นำเข้า Annotated ใช้ประกาศ dependency

from fastapi import APIRouter, Depends, HTTPException, status  # นำเข้าเครื่องมือสร้างกลุ่ม endpoint และการตอบ error
from fastapi.security import OAuth2PasswordRequestForm  # นำเข้าฟอร์ม login มาตรฐาน (username + password)
from sqlmodel import select  # นำเข้า select สำหรับค้นหาข้อมูลในฐานข้อมูล

from app.models import Token, User, UserCreate, UserPublic  # นำเข้าตารางและรูปแบบข้อมูลของผู้ใช้
from app.security import CurrentUser, SessionDep, create_access_token, hash_password, verify_password  # เครื่องมือความปลอดภัย

router = APIRouter(prefix="/auth", tags=["auth"])  # กลุ่ม endpoint ที่ขึ้นต้นด้วย /auth


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)  # POST /auth/register สมัครผู้ใช้
def register(data: UserCreate, session: SessionDep):  # รับข้อมูลสมัครที่ผ่านการตรวจของ Pydantic แล้ว
    existing = session.exec(select(User).where(User.username == data.username)).first()  # หาว่าชื่อนี้มีคนใช้แล้วหรือยัง
    if existing is not None:  # ชื่อผู้ใช้ซ้ำ
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="ชื่อผู้ใช้นี้มีอยู่แล้ว")  # ตอบ 409
    user = User(  # สร้างผู้ใช้ใหม่
        username=data.username,  # ชื่อผู้ใช้ตามที่สมัคร
        full_name=data.full_name,  # ชื่อจริงตามที่สมัคร
        hashed_password=hash_password(data.password),  # เก็บเฉพาะ hash ของรหัสผ่าน
        role="student",  # ผู้สมัครเองเป็น student เสมอ ป้องกันการสมัครเป็น staff เอง
    )
    session.add(user)  # เตรียมบันทึกผู้ใช้ใหม่
    session.commit()  # บันทึกลงฐานข้อมูลจริง
    session.refresh(user)  # อ่านค่าล่าสุดกลับมา เพื่อให้ได้ id
    return user  # ส่งข้อมูลผู้ใช้กลับไป (response_model ตัด hashed_password ออกให้)


@router.post("/login", response_model=Token)  # POST /auth/login รับ JWT
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], session: SessionDep):  # รับ username/password แบบฟอร์ม
    user = session.exec(select(User).where(User.username == form.username)).first()  # หาผู้ใช้จากชื่อที่กรอก
    if user is None or not verify_password(form.password, user.hashed_password):  # ไม่พบผู้ใช้ หรือรหัสผ่านผิด
        raise HTTPException(  # ตอบ error เดียวกันทั้งสองกรณี เพื่อไม่บอกคนร้ายว่าชื่อผู้ใช้มีอยู่จริง
            status_code=status.HTTP_401_UNAUTHORIZED,  # 401 คือยืนยันตัวตนไม่สำเร็จ
            detail="ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",  # ข้อความที่ผู้ใช้จะเห็น
            headers={"WWW-Authenticate": "Bearer"},  # บอก client ว่าระบบนี้ใช้ token แบบ Bearer
        )
    return Token(access_token=create_access_token(user.username))  # สร้าง JWT แล้วส่งกลับไป


@router.get("/me", response_model=UserPublic)  # GET /auth/me ดูข้อมูลผู้ใช้ที่ login อยู่
def read_me(user: CurrentUser):  # FastAPI หาผู้ใช้จาก token ให้ก่อนเรียกฟังก์ชันนี้
    return user  # ส่งข้อมูลผู้ใช้กลับไป
