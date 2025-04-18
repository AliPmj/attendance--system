from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import numpy as np
from sklearn.cluster import KMeans
from prophet import Prophet
import pandas as pd

app = FastAPI()

class ShiftData(BaseModel):
    employee_id: int
    availability: List[int]
    workload: float

class FraudDetection(BaseModel):
    user_id: int
    attendance_data: List[dict]

class DemandPrediction(BaseModel):
    historical_data: List[dict]  # {date, value}

@app.post("/optimize-shifts/")
async def optimize_shifts(data: List[ShiftData]):
    X = np.array([[d.workload, len(d.availability)] for d in data])
    kmeans = KMeans(n_clusters=3)
    kmeans.fit(X)
    return {"shifts": kmeans.labels_.tolist()}

@app.post("/detect-fraud/")
async def detect_fraud(data: FraudDetection):
    timestamps = [pd.to_datetime(t["timestamp"]) for t in data.attendance_data]
    if len(timestamps) < 2:
        return {"fraud": False}
    intervals = [(timestamps[i+1] - timestamps[i]).total_seconds() / 60 for i in range(len(timestamps)-1)]
    mean_interval = np.mean(intervals)
    std_interval = np.std(intervals)
    anomalies = [i for i in intervals if abs(i - mean_interval) > 2 * std_interval]
    return {"fraud": len(anomalies) > 0}

@app.post("/predict-demand/")
async def predict_demand(data: DemandPrediction):
    df = pd.DataFrame(data.historical_data)
    df['ds'] = pd.to_datetime(df['date'])
    df['y'] = df['value']
    model = Prophet()
    model.fit(df)
    future = model.make_future_dataframe(periods=7)
    forecast = model.predict(future)
    return {"forecast": forecast[['ds', 'yhat']].to_dict(orient="records")}