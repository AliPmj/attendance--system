from sqlalchemy.orm import Session
from database import SessionLocal
from fastapi import HTTPException

def delete_user_data(user_id: int):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        db.query(Attendance).filter(Attendance.user_id == user_id).delete()
        db.query(Leave).filter(Leave.user_id == user_id).delete()
        db.delete(user)
        db.commit()
        return {"status": "deleted"}
    finally:
        db.close()