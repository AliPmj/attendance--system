from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import SessionLocal, engine, Base
import qrcode
import io
from sklearn.ensemble import RandomForestClassifier
import pandas as pd
import numpy as np
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = FastAPI()

# Database Models
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from datetime import datetime

class Menu(Base):
    __tablename__ = "menus"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    calories = Column(Float)
    allergens = Column(String)
    group = Column(String)

class Reservation(Base):
    __tablename__ = "reservations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    menu_id = Column(Integer, ForeignKey("menus.id"))
    quantity = Column(Integer)
    date = Column(DateTime)
    is_guest = Column(Boolean, default=False)

class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    ingredient = Column(String)
    quantity = Column(Float)
    threshold = Column(Float)

class WasteReport(Base):
    __tablename__ = "waste_reports"
    id = Column(Integer, primary_key=True, index=True)
    menu_id = Column(Integer, ForeignKey("menus.id"))
    quantity_wasted = Column(Float)
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Pydantic Models
class MenuCreate(BaseModel):
    name: str
    calories: float
    allergens: str
    group: str

class ReservationCreate(BaseModel):
    user_id: int
    menu_id: int
    quantity: int
    date: datetime
    is_guest: bool

class InventoryUpdate(BaseModel):
    ingredient: str
    quantity: float
    threshold: float

class WasteReportCreate(BaseModel):
    menu_id: int
    quantity_wasted: float

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# AI Menu Recommendation
def recommend_menu(user_id: int, db: Session) -> int:
    reservations = db.query(Reservation).filter(Reservation.user_id == user_id).all()
    if not reservations:
        return db.query(Menu).first().id
    data = [(r.menu_id, r.quantity) for r in reservations]
    df = pd.DataFrame(data, columns=["menu_id", "quantity"])
    X = df[["quantity"]]
    y = df["menu_id"]
    clf = RandomForestClassifier()
    clf.fit(X, y)
    return clf.predict([[1]])[0]

# Routes
@app.post("/menus/")
async def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    db_menu = Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return menu

@app.post("/reservations/")
async def create_reservation(reservation: ReservationCreate, db: Session = Depends(get_db)):
    if reservation.is_guest:
        # Placeholder for manager approval
        pass
    db_reservation = Reservation(**reservation.dict())
    db.add(db_reservation)
    db.commit()
    qr = qrcode.QRCode()
    qr.add_data(f"reservation:{db_reservation.id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return {"status": "reserved", "qr_code": buffer.getvalue()}

@app.post("/inventory/")
async def update_inventory(inventory: InventoryUpdate, db: Session = Depends(get_db)):
    db_inventory = Inventory(**inventory.dict())
    db.add(db_inventory)
    db.commit()
    if db_inventory.quantity < db_inventory.threshold:
        # Placeholder for warehouse alert
        pass
    return {"status": "updated"}

@app.post("/waste-reports/")
async def report_waste(report: WasteReportCreate, db: Session = Depends(get_db)):
    db_report = WasteReport(**report.dict())
    db.add(db_report)
    db.commit()
    return {"status": "reported"}

@app.get("/reservations/")
async def get_reservations(db: Session = Depends(get_db)):
    return db.query(Reservation).all()

@app.get("/recommend-menu/{user_id}")
async def get_recommended_menu(user_id: int, db: Session = Depends(get_db)):
    menu_id = recommend_menu(user_id, db)
    return {"menu_id": menu_id}

@app.get("/tokens/pdf/{reservation_id}")
async def generate_token_pdf(reservation_id: int, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Reservation not found")
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.drawString(100, 750, f"Token for Reservation {reservation_id}")
    c.drawString(100, 730, f"User ID: {reservation.user_id}, Menu ID: {reservation.menu_id}")
    qr = qrcode.QRCode()
    qr.add_data(f"reservation:{reservation_id}")
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img.save("token.png")
    c.drawImage("token.png", 100, 600, width=100, height=100)
    c.save()
    buffer.seek(0)
    return {"pdf": buffer.getvalue()}
# (Add to existing main.py)
class Sustainability(Base):
    __tablename__ = "sustainability"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    used_recyclable = Column(Boolean)
    reward_points = Column(Integer, default=0)

class SustainabilityUpdate(BaseModel):
    user_id: int
    used_recyclable: bool

@app.post("/sustainability/")
async def update_sustainability(update: SustainabilityUpdate, db: Session = Depends(get_db)):
    db_sustainability = Sustainability(user_id=update.user_id, used_recyclable=update.used_recyclable, reward_points=10 if update.used_recyclable else 0)
    db.add(db_sustainability)
    db.commit()
    return {"status": "updated", "reward_points": db_sustainability.reward_points}