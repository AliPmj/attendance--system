from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import cv2
import numpy as np
from database import SessionLocal, engine, Base
from paho.mqtt import client as mqtt_client
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64
import os
import requests

app = FastAPI()

MQTT_BROKER = "broker.hivemq.com"
MQTT_PORT = 1883
MQTT_TOPIC = "access-control/iot"
CALENDAR_API_URL = "http://mock-calendar:8081/api"  # Mock calendar endpoint

# Database Models
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

class AccessRule(Base):
    __tablename__ = "access_rules"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    location = Column(String)
    time_start = Column(DateTime)
    time_end = Column(DateTime)
    is_temporary = Column(Boolean, default=False)
    two_factor_required = Column(Boolean, default=False)

class AccessLog(Base):
    __tablename__ = "access_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    location = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    is_vehicle = Column(Boolean)

class Visitor(Base):
    __tablename__ = "visitors"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    qr_code = Column(String, unique=True)
    expiry = Column(DateTime)
    meeting_id = Column(Integer, nullable=True)

class ParkingSpot(Base):
    __tablename__ = "parking_spots"
    id = Column(Integer, primary_key=True, index=True)
    spot_number = Column(Integer)
    is_occupied = Column(Boolean, default=False)
    user_id = Column(Integer, nullable=True)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class AccessRuleCreate(BaseModel):
    user_id: int
    location: str
    time_start: datetime
    time_end: datetime
    is_temporary: bool
    two_factor_required: bool

class AccessLogCreate(BaseModel):
    user_id: int
    location: str
    is_vehicle: bool

class VisitorCreate(BaseModel):
    name: str
    expiry: datetime
    meeting_id: Optional[int]

class ParkingReservation(BaseModel):
    user_id: int
    spot_number: int

# Encryption
def encrypt_data(data: str, key: bytes = b"your-32-byte-key-here-1234567890") -> str:
    cipher = AES.new(key, AES.MODE_CBC)
    ct_bytes = cipher.encrypt(pad(data.encode(), AES.block_size))
    iv = base64.b64encode(cipher.iv).decode('utf-8')
    ct = base64.b64encode(ct_bytes).decode('utf-8')
    return f"{iv}:{ct}"

# MQTT Setup
mqtt_client = mqtt_client.Client()
mqtt_client.connect(MQTT_BROKER, MQTT_PORT)
mqtt_client.subscribe(MQTT_TOPIC)

# Recognition (Placeholders)
def recognize_plate(image: np.ndarray) -> str:
    return "ABC123"

def verify_face(image: np.ndarray, stored_encoding: str, low_light: bool = False) -> bool:
    # Placeholder for DeepFace with low-light support
    return True

def verify_multi_person(images: List[np.ndarray], stored_encodings: List[str]) -> List[bool]:
    # Placeholder for multi-person recognition
    return [True] * len(images)

# Calendar Integration
def link_visitor_to_meeting(visitor_id: int, meeting_id: int):
    try:
        requests.post(f"{CALENDAR_API_URL}/meetings/{meeting_id}/visitors", json={"visitor_id": visitor_id})
    except:
        pass  # Mock integration

# Routes
@app.post("/access-rules/")
async def create_access_rule(rule: AccessRuleCreate, db: Session = Depends(get_db)):
    db_rule = AccessRule(**rule.dict())
    db.add(db_rule)
    db.commit()
    # AI-suggested rules
    response = requests.post("http://ai-engine:8004/detect-fraud/", json={"user_id": rule.user_id, "attendance_data": []})
    if response.json()["fraud"]:
        mqtt_client.publish(MQTT_TOPIC, f"Suspicious rule for user {rule.user_id}")
    db.refresh(db_rule)
    return rule

@app.post("/access-logs/")
async def log_access(log: AccessLogCreate, db: Session = Depends(get_db)):
    if not opt_out_tracking:
        encrypted_log = encrypt_data(f"{log.user_id}:{log.location}")
        db_log = AccessLog(**log.dict())
        db.add(db_log)
        db.commit()
        mqtt_client.publish(MQTT_TOPIC, f"Access: {log.user_id} at {log.location}")
    return {"status": "logged"}

@app.post("/visitors/")
async def create_visitor(visitor: VisitorCreate, db: Session = Depends(get_db)):
    qr_code = f"visitor:{visitor.name}:{visitor.expiry}"
    db_visitor = Visitor(name=visitor.name, qr_code=qr_code, expiry=visitor.expiry, meeting_id=visitor.meeting_id)
    db.add(db_visitor)
    db.commit()
    if visitor.meeting_id:
        link_visitor_to_meeting(db_visitor.id, visitor.meeting_id)
    # Placeholder for email/SMS
    return {"qr_code": qr_code}

@app.post("/parking/")
async def reserve_parking(reservation: ParkingReservation, db: Session = Depends(get_db)):
    spot = db.query(ParkingSpot).filter(ParkingSpot.spot_number == reservation.spot_number).first()
    if spot and not spot.is_occupied:
        spot.is_occupied = True
        spot.user_id = reservation.user_id
        db.commit()
        return {"status": "reserved"}
    raise HTTPException(status_code=400, detail="Spot unavailable")

@app.get("/access-logs/")
async def get_access_logs(db: Session = Depends(get_db)):
    return db.query(AccessLog).all()

@app.post("/verify-plate/")
async def verify_plate(file: UploadFile = File(...), db: Session = Depends(get_db)):
    image_data = await file.read()
    nparr = np.frombuffer(image_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    plate = recognize_plate(img)
    return {"plate": plate, "status": "verified"}

@app.post("/verify-faces/")
async def verify_faces(files: List[UploadFile] = File(...), db: Session = Depends(get_db)):
    images = [cv2.imdecode(np.frombuffer(await f.read(), np.uint8), cv2.IMREAD_COLOR) for f in files]
    users = db.query(User).all()
    results = verify_multi_person(images, [u.face_encoding for u in users])
    return {"results": results}

@app.post("/emergency/fire-alarm/")
async def fire_alarm(db: Session = Depends(get_db)):
    mqtt_client.publish(MQTT_TOPIC, "Fire alarm: Open all doors")
    return {"status": "doors opened"}

@app.get("/emergency/headcount/")
async def headcount(db: Session = Depends(get_db)):
    logs = db.query(AccessLog).filter(AccessLog.timestamp >= datetime.utcnow() - timedelta(hours=1)).all()
    headcount = len(set(log.user_id for log in logs))
    return {"headcount": headcount}
# (Add to existing main.py)
@app.post("/energy-optimization/")
async def optimize_energy(state: bool):
    mqtt_client.publish(MQTT_TOPIC, f"Device power: {'on' if state else 'off'}")
    return {"status": "optimized"}