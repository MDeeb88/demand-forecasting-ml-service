import pandas as pd
import numpy as np
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OrdinalEncoder
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error


df = pd.read_csv("enriched_demand.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values("Date")

features = [
    "Product_Code",
    "Warehouse",
    "Product_Category",
    "season",
    "month",
    "quarter",
    "year",
    "is_holiday_season",
    "lag_1",
    "lag_2",
    "lag_3",
    "lag_6",
    "rolling_mean_3",
    "rolling_mean_6",
    "Unit_Price"
]

target = "Order_Demand"

train = df[df["Date"] < "2016-01-01"]
test = df[df["Date"] >= "2016-01-01"]

X_train = train[features]
y_train = train[target]

X_test = test[features]
y_test = test[target]

baseline_pred = X_test["lag_1"]
baseline_mae = mean_absolute_error(y_test, baseline_pred)
baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))

cat_cols = [
    "Product_Code",
    "Warehouse",
    "Product_Category",
    "season"
]

preprocessor = ColumnTransformer(
    transformers=[
        (
            "cat",
            OrdinalEncoder(
                handle_unknown="use_encoded_value",
                unknown_value=-1
            ),
            cat_cols
        )
    ],
    remainder="passthrough"
)

model = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("regressor", HistGradientBoostingRegressor(
        max_iter=100,
        learning_rate=0.08,
        max_leaf_nodes=31,
        random_state=42
    ))
])

model.fit(X_train, y_train)

pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
rmse = np.sqrt(mean_squared_error(y_test, pred))

print("Baseline MAE:", baseline_mae)
print("Baseline RMSE:", baseline_rmse)
print("Model MAE:", mae)
print("Model RMSE:", rmse)
print("MAE Improvement:", baseline_mae - mae)

joblib.dump(model, "demand_forecast_model.joblib")
print("Model saved successfully.")