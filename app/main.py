from pathlib import Path
from typing import Dict

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel


app = FastAPI(
    title="Demand Forecasting ML Service",
    description="API for demand prediction with simple user credit billing.",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "demand_forecast_model.joblib"
model = joblib.load(MODEL_PATH)


users: Dict[str, dict] = {}
PREDICTION_COST = 5


class RegisterInput(BaseModel):
    username: str
    password: str


class LoginInput(BaseModel):
    username: str
    password: str


class TopUpInput(BaseModel):
    credits: int


class PredictionInput(BaseModel):
    Product_Code: str
    Warehouse: str
    Product_Category: str
    season: str
    month: int
    quarter: int
    year: int
    is_holiday_season: int
    lag_1: float
    lag_2: float
    lag_3: float
    lag_6: float
    rolling_mean_3: float
    rolling_mean_6: float
    Unit_Price: float


def get_current_user(token: str):
    if token not in users:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return users[token]


@app.get("/")
def home():
    return {"message": "Demand Forecasting API is running", "docs": "/docs"}


@app.post("/register")
def register(data: RegisterInput):
    if data.username in users:
        raise HTTPException(status_code=400, detail="Username already exists")

    users[data.username] = {
        "username": data.username,
        "password": data.password,
        "credits": 100,
        "prediction_history": [],
        "transactions": [
            {
                "type": "initial_bonus",
                "credits": 100,
                "balance_after": 100
            }
        ]
    }

    return {
        "message": "User registered successfully",
        "username": data.username,
        "starting_credits": 100
    }


@app.post("/login")
def login(data: LoginInput):
    user = users.get(data.username)

    if not user or user["password"] != data.password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return {
        "message": "Login successful",
        "token": data.username,
        "credits": user["credits"]
    }


@app.get("/balance")
def get_balance(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"username": user["username"], "credits": user["credits"]}


@app.post("/topup")
def topup(data: TopUpInput, authorization: str = Header(None)):
    user = get_current_user(authorization)

    if data.credits <= 0:
        raise HTTPException(status_code=400, detail="Credits must be greater than zero")

    user["credits"] += data.credits

    transaction = {
        "type": "topup",
        "credits": data.credits,
        "balance_after": user["credits"]
    }

    user["transactions"].append(transaction)

    return {
        "message": "Credits added successfully",
        "added_credits": data.credits,
        "new_balance": user["credits"]
    }


@app.post("/predict")
def predict(input_data: PredictionInput, authorization: str = Header(None)):
    user = get_current_user(authorization)

    if user["credits"] < PREDICTION_COST:
        raise HTTPException(
            status_code=402,
            detail="Insufficient credits. Please buy more credits."
        )

    data = pd.DataFrame([input_data.model_dump()])
    prediction = model.predict(data)[0]

    predicted_demand = max(0, round(float(prediction), 2))
    predicted_revenue = round(predicted_demand * input_data.Unit_Price, 2)

    user["credits"] -= PREDICTION_COST

    result = {
        "product_code": input_data.Product_Code,
        "warehouse": input_data.Warehouse,
        "predicted_demand": predicted_demand,
        "unit_price": input_data.Unit_Price,
        "predicted_revenue": predicted_revenue,
        "credits_charged": PREDICTION_COST,
        "remaining_credits": user["credits"]
    }

    user["prediction_history"].append(result)

    user["transactions"].append({
        "type": "prediction_charge",
        "credits": -PREDICTION_COST,
        "balance_after": user["credits"]
    })

    return result


@app.get("/history")
def prediction_history(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"username": user["username"], "history": user["prediction_history"]}


@app.get("/transactions")
def transactions(authorization: str = Header(None)):
    user = get_current_user(authorization)
    return {"username": user["username"], "transactions": user["transactions"]}


@app.post("/promo/{code}")
def apply_promo(code: str, authorization: str = Header(None)):
    user = get_current_user(authorization)

    promo_codes = {
        "WELCOME100": 100,
        "STUDENT50": 50
    }

    if code not in promo_codes:
        raise HTTPException(status_code=400, detail="Invalid promo code")

    added = promo_codes[code]
    user["credits"] += added

    user["transactions"].append({
        "type": "promo",
        "code": code,
        "credits": added,
        "balance_after": user["credits"]
    })

    return {
        "message": "Promo code applied",
        "added_credits": added,
        "new_balance": user["credits"]
    }