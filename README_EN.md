# Demand Forecasting ML Service

## Overview

Demand Forecasting ML Service is a machine learning web application designed to forecast product demand and estimate business revenue using historical product demand data.

### Features

- Machine Learning forecasting
- FastAPI backend
- Streamlit dashboard
- Billing and credit system
- Fake checkout simulation
- Docker deployment
- English / Russian language support
- Revenue forecasting

---

## Technologies Used

- Python
- FastAPI
- Streamlit
- Scikit-learn
- Pandas
- NumPy
- Docker
- Docker Compose

---

## Machine Learning Pipeline

### Data Preparation

- Date conversion
- Missing value removal
- Monthly aggregation
- Feature engineering

### Features Used

- Product code
- Warehouse
- Product category
- Month / season
- Lag features
- Rolling averages
- Simulated pricing

### Model

- HistGradientBoostingRegressor

### Metrics

- MAE
- RMSE
- Baseline comparison

---

## Dashboard Features

- Product filtering
- Warehouse filtering
- Revenue analysis
- Demand forecasting
- Prediction graphs
- Billing transactions
- Advanced forecasting options
- Multilingual support

---

## Billing System

The application contains a simulated SaaS-style billing system.

Features:

- Paid predictions
- Credit deduction
- Fake checkout popup
- Free puzzle reward credits
- Credit transaction history

---

## Docker Setup

Run the application using:

```bash
docker-compose up --build
```

Dashboard:

http://127.0.0.1:8501

API Docs:

http://127.0.0.1:8000/docs

---

## Project Structure

```text
demand-forecasting-ml-service/
│
├── app/
│   └── main.py
│
├── dashboard.py
├── translations.py
├── train_model.py
│
├── enriched_demand.csv
├── model_predictions.csv
├── demand_forecast_model.joblib
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
├── .gitignore
└── Launch_Demand_Forecasting_App.bat
```

---

## User Workflow

1. Register
2. Login
3. Buy credits
4. Select products
5. Configure forecast
6. Run prediction
7. View graphs and analytics

---

## Language Support

Supported languages:

- English
- Russian

---

## Notes

- User accounts and credits are stored temporarily in memory.
- Unit prices are simulated for educational purposes.

---

## Future Improvements

- PostgreSQL integration
- JWT authentication
- AI-generated business reviews
- Automated tests
- Cloud deployment
