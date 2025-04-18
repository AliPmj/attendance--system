from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import cv2
import numpy as np
from database import SessionLocal, engine, Base
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from telegram import Bot
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import pandas as pd
import io
import requests

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
TELEGRAM_BOT_TOKEN = "your-telegram-bot-token"
TELEGRAM_CHAT_ID = "your-chat-id"
JIRA_API_URL = "http://mock-jira:8080/api"  # Mock Jira endpoint

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
telegram_bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Database Models
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, ForeignKey

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    face_encoding = Column(String)
    fingerprint = Column(String)
    qr_code = Column(String, unique=True)
    hashed_password = Column(String)
    nfc_tag = Column(String)
    role = Column(String, default="employee")  # employee, manager, hr

class Attendance(Base):
    __tablename__ = "attendances"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_entry = Column(Boolean)
    penalty = Column(Float, default=0.0)
    reward = Column(Float, default=0.0)

class Leave(Base):
    __tablename__ = "leaves"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    status = Column(String, default="pending")  # pending, manager_approved, hr_approved, rejected
    substitute_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    manager_approval = Column(Boolean, default=False)
    hr_approval = Column(Boolean, default=False)

class Shift(Base):
    __tablename__ = "shifts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    start_time = Column(DateTime)
    end_time = Column(DateTime)
    is_remote = Column(Boolean, default=False)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    name: str
    qr_code: str
    password: str
    nfc_tag: Optional[str]
    role: Optional[str]

class AttendanceRecord(BaseModel):
    user_id: int
    is_entry: bool

class LeaveRequest(BaseModel):
    user_id: int
    start_date: datetime
    end_date: datetime
    substitute_id: Optional[int]

class ShiftCreate(BaseModel):
    user_id: int
    start_time: datetime
    end_time: datetime
    is_remote: bool

class Token(BaseModel):
    access_token: str
    token_type: str

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    return user

# Verification Functions (Placeholders)
def verify_face(image: np.ndarray, stored_encoding: str) -> bool:
    return True

def verify_fingerprint(data: bytes, stored_fingerprint: str) -> bool:
    return True

def verify_nfc(tag: str, stored_tag: str) -> bool:
    return tag == stored_tag

# Penalties/Rewards
def calculate_penalties_rewards(attendance: Attendance, shift: Shift) -> tuple:
    if not shift:
        return 0.0, 0.0
    expected_time = shift.start_time if attendance.is_entry else shift.end_time
    actual_time = attendance.timestamp
    delta = (actual_time - expected_time).total_seconds() / 60
    if attendance.is_entry and delta > 15:  # Late by 15+ minutes
        return 10.0, 0.0  # $10 penalty
    elif abs(delta) <= 5:  # On time
        return 0.0, 5.0  # $5 reward
    return 0.0, 0.0

# Jira Integration
def log_task_hours(user_id: int, hours: float):
    try:
        requests.post(f"{JIRA_API_URL}/tasks", json={"user_id": user_id, "hours": hours})
    except:
        pass  # Mock integration

# Fraud Detection
def detect_fraud(attendances: List[dict]) -> bool:
    timestamps = [a["timestamp"] for a in attendances]
    if len(timestamps) < 2:
        return False
    intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() / 60 for i in range(len(timestamps)-1)]
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    anomalies = [i for i in intervals if abs(i - mean_interval) > 2 * std_interval]
    return len(anomalies) > 0

# Routes
@app.post("/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.name == form_data.username).first()
    if not user or not pwd_context.verify(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = jwt.encode({"sub": str(user.id)}, SECRET_KEY, algorithm=ALGORITHM)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/users/", response_model=UserCreate)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    hashed_password = pwd_context.hash(user.password)
    db_user = User(name=user.name, qr_code=user.qr_code, hashed_password=hashed_password, nfc_tag=user.nfc_tag, role=user.role)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return user

@app.post("/attendance/")
async def record_attendance(record: AttendanceRecord, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shift = db.query(Shift).filter(Shift.user_id == record.user_id, Shift.start_time <= datetime.utcnow(), Shift.end_time >= datetime.utcnow()).first()
    penalty, reward = calculate_penalties_rewards(Attendance(**record.dict()), shift)
    db_attendance = Attendance(user_id=record.user_id, is_entry=record.is_entry, penalty=penalty, reward=reward)
    db.add(db_attendance)
    db.commit()
    # Fraud detection
    recent_attendances = db.query(Attendance).filter(Attendance.user_id == record.user_id).order_by(Attendance.timestamp.desc()).limit(10).all()
    if detect_fraud([{"timestamp": a.timestamp} for a in recent_attendances]):
        await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Fraud detected for user {record.user_id}")
    # Notify user
    user = db.query(User).filter(User.id == record.user_id).first()
    await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Attendance recorded for {user.name}: {'Entry' if record.is_entry else 'Exit'}")
    # Log to Jira
    hours = 8.0 if not shift or shift.is_remote else 8.0  # Simplified
    log_task_hours(record.user_id, hours)
    return {"status": "recorded", "penalty": penalty, "reward": reward}

@app.post("/verify-face/")
async def verify_face_endpoint(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    image_data = await file.read()
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if verify_face(img, user.face_encoding):
        return {"status": "verified"}
    raise HTTPException(status_code=401, detail="Face verification failed")

@app.post("/verify-fingerprint/")
async def verify_fingerprint_endpoint(user_id: int, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    fingerprint_data = await file.read()
    if verify_fingerprint(fingerprint_data, user.fingerprint):
        return {"status": "verified"}
    raise HTTPException(status_code=401, detail="Fingerprint verification failed")

@app.post("/verify-nfc/")
async def verify_nfc_endpoint(user_id: int, nfc_tag: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if verify_nfc(nfc_tag, user.nfc_tag):
        return {"status": "verified"}
    raise HTTPException(status_code=401, detail="NFC verification failed")

@app.post("/leaves/")
async def request_leave(leave: LeaveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_leave = Leave(**leave.dict())
    db.add(db_leave)
    db.commit()
    # Suggest substitute
    substitute = db.query(User).filter(User.id != leave.user_id, User.role != "hr").first()
    await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Leave requested by user {leave.user_id}. Suggested substitute: {substitute.name}")
    return {"status": "requested"}

@app.post("/leaves/approve/")
async def approve_leave(leave_id: int, role: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != role:
        raise HTTPException(status_code=403, detail="Unauthorized")
    leave = db.query(Leave).filter(Leave.id == leave_id).first()
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    if role == "manager":
        leave.manager_approval = True
    elif role == "hr":
        leave.hr_approval = True
    if leave.manager_approval and leave.hr_approval:
        leave.status = "approved"
    db.commit()
    await telegram_bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"Leave {leave_id} {leave.status} by {role}")
    return {"status": leave.status}

@app.post("/shifts/")
async def create_shift(shift: ShiftCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    db_shift = Shift(**shift.dict())
    db.add(db_shift)
    db.commit()
    return {"status": "created"}

@app.post("/shifts/emergency/")
async def emergency_shift(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    shift = db.query(Shift).filter(Shift.user_id == user_id, Shift.start_time <= datetime.utcnow(), Shift.end_time >= datetime.utcnow()).first()
    if shift:
        shift.end_time = datetime.utcnow() + timedelta(hours=1)  # Adjust shift
        db.commit()
    return {"status": "adjusted"}

@app.get("/attendances/")
async def get_attendances(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Attendance).all()

@app.get("/reports/attendance/pdf")
async def generate_attendance_report(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, "Attendance Report")
    attendances = db.query(Attendance).all()
    y = 700
    for a in attendances:
        c.drawString(100, y, f"User {a.user_id}: {'Entry' if a.is_entry else 'Exit'} at {a.timestamp}, Penalty: {a.penalty}, Reward: {a.reward}")
        y -= 20
    c.save()
    buffer.seek(0)
    return {"pdf": buffer.getvalue()}

@app.get("/reports/attendance/excel")
async def generate_attendance_excel(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    attendances = db.query(Attendance).all()
    df = pd.DataFrame([(a.user_id, a.is_entry, a.timestamp, a.penalty, a.reward) for a in attendances], columns=["User ID", "Is Entry", "Timestamp", "Penalty", "Reward"])
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False)
    buffer.seek(0)
    return {"excel": buffer.getvalue()}

@app.get("/predict-leaves/")
async def predict_leaves(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    leaves = db.query(Leave).all()
    df = pd.DataFrame([(l.start_date, 1) for l in leaves], columns=["ds", "y"])
    df['ds'] = pd.to_datetime(df['ds'])
    response = requests.post("http://ai-engine:8004/predict-demand/", json={"historical_data": df.to_dict(orient="records")})
    return response.json()