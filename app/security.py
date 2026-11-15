from datetime import datetime, timedelta, timezone  # นำเข้าเครื่องมือวันเวลา ใช้กำหนดวันหมดอายุของ JWT
from typing import Annotated  # นำเข้า Annotated ใช้ประกาศ dependency ให้อ่านง่าย

import jwt  # นำเข้า PyJWT ใช้สร้างและตรวจ JWT
from fastapi import Depends, HTTPException, status  # นำเข้าเครื่องมือของ FastAPI สำหรับ dependency และการตอบ error
from fastapi.security import OAuth2PasswordBearer  # นำเข้าตัวอ่าน token จาก header Authorization
from pwdlib import PasswordHash  # นำเข้าเครื่องมือ hash รหัสผ่าน
from sqlmodel import Session, select  # นำเข้า Session และ select สำหรับค้นหาข้อมูลในฐานข้อมูล

from app.config import settings  # นำเข้าค่าตั้งค่า เพื่ออ่าน secret_key และอายุ token
from app.database import get_session  # นำเข้า dependency ที่ให้ session ฐานข้อมูล
from app.models import User  # นำเข้าตาราง User เพื่อค้นหาผู้ใช้จาก token

password_hash = PasswordHash.recommended()  # สร้างตัว hash รหัสผ่านด้วยค่าที่แนะนำ (argon2)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")  # บอก FastAPI ว่ารับ token จาก endpoint /auth/login


def hash_password(password: str) -> str:  # แปลงรหัสผ่านจริงเป็น hash ก่อนบันทึกลงฐานข้อมูล
    return password_hash.hash(password)  # คืนค่า hash ซึ่งย้อนกลับเป็นรหัสผ่านจริงไม่ได้


def verify_password(password: str, hashed_password: str) -> bool:  # ตรวจว่ารหัสผ่านที่พิมพ์มาตรงกับ hash ที่เก็บไว้หรือไม่
    return password_hash.verify(password, hashed_password)  # คืน True ถ้าตรง และ False ถ้าไม่ตรง


def create_access_token(username: str) -> str:  # สร้าง JWT ให้ผู้ใช้ที่ login สำเร็จ
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)  # คำนวณเวลาหมดอายุ
    payload = {"sub": username, "exp": expire}  # ข้อมูลใน token: sub คือเจ้าของ token และ exp คือเวลาหมดอายุ
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)  # เซ็น token ด้วยกุญแจลับแล้วคืนเป็นข้อความ


SessionDep = Annotated[Session, Depends(get_session)]  # ตั้งชื่อย่อให้ "session ฐานข้อมูลที่ได้จาก get_session"


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: SessionDep) -> User:  # dependency หาผู้ใช้จาก token
    credentials_error = HTTPException(  # เตรียม error 401 ไว้ใช้เมื่อ token ไม่ถูกต้อง
        status_code=status.HTTP_401_UNAUTHORIZED,  # 401 แปลว่ายังยืนยันตัวตนไม่สำเร็จ
        detail="token ไม่ถูกต้องหรือหมดอายุ",  # ข้อความอธิบายที่ผู้ใช้จะเห็น
        headers={"WWW-Authenticate": "Bearer"},  # บอก client ว่าต้องแนบ token แบบ Bearer
    )
    try:  # ลองถอดรหัส token ถ้าผิดรูปแบบหรือหมดอายุ จะเกิด error
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])  # ตรวจลายเซ็นและวันหมดอายุ
    except jwt.InvalidTokenError:  # จับทุกกรณีที่ token ใช้ไม่ได้ รวมถึงหมดอายุ
        raise credentials_error  # ตอบ 401 กลับไป
    username = payload.get("sub")  # อ่านชื่อผู้ใช้ที่ฝังไว้ใน token
    user = session.exec(select(User).where(User.username == username)).first()  # ค้นหาผู้ใช้ที่มีชื่อตรงกับใน token
    if user is None:  # ถ้าไม่พบผู้ใช้ เช่น ถูกลบไปแล้ว
        raise credentials_error  # ตอบ 401 กลับไป
    return user  # ส่งผู้ใช้ให้ฟังก์ชันของ endpoint ใช้งานต่อ


CurrentUser = Annotated[User, Depends(get_current_user)]  # ตั้งชื่อย่อให้ "ผู้ใช้ที่ login อยู่"


def require_staff(user: CurrentUser) -> User:  # dependency ที่ยอมให้ผ่านเฉพาะผู้ใช้ role staff
    if user.role != "staff":  # ถ้าไม่ใช่ staff
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="ต้องเป็น staff เท่านั้น")  # 403 คือรู้ว่าเป็นใคร แต่ไม่มีสิทธิ์
    return user  # ถ้าเป็น staff ส่งผู้ใช้ต่อไปตามปกติ


StaffUser = Annotated[User, Depends(require_staff)]  # ตั้งชื่อย่อให้ "ผู้ใช้ที่เป็น staff"
