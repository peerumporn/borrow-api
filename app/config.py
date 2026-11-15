from pydantic_settings import BaseSettings, SettingsConfigDict  # นำเข้าเครื่องมืออ่านค่าตั้งค่าจากไฟล์ .env และ environment variable


class Settings(BaseSettings):  # คลาสเก็บค่าตั้งค่าทั้งหมดของแอป แต่ละฟิลด์คือค่าหนึ่งค่าใน .env
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")  # บอกให้อ่านค่าจากไฟล์ .env ที่อยู่ในโฟลเดอร์ที่รันคำสั่ง

    database_url: str = "sqlite:///./borrow.db"  # ที่อยู่ฐานข้อมูล ถ้าไม่ตั้งค่าไว้ จะใช้ไฟล์ SQLite ในเครื่องตัวเอง
    secret_key: str = "change-me-in-env-use-at-least-32-characters"  # กุญแจลับเซ็น JWT ค่าปลอม ต้องยาว 32 ตัวขึ้นไปและตั้งค่าจริงใน .env
    algorithm: str = "HS256"  # วิธีเซ็น JWT ที่ใช้กุญแจลับตัวเดียวทั้งตอนเซ็นและตอนตรวจ
    access_token_expire_minutes: int = 30  # อายุของ JWT เป็นนาที หมดเวลาแล้วต้อง login ใหม่
    staff_username: str = "admin"  # ชื่อผู้ใช้ staff คนแรกที่ระบบสร้างให้ตอนเริ่มทำงาน
    staff_password: str = "change-me-in-env"  # รหัสผ่านของ staff คนแรก ค่านี้เป็นค่าปลอม ต้องตั้งค่าจริงใน .env


settings = Settings()  # สร้างอ็อบเจกต์ค่าตั้งค่าไว้ครั้งเดียว ไฟล์อื่นนำเข้าตัวแปรนี้ไปใช้
