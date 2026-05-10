import streamlit as st
import requests
import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
from translations import TEXT


API_URL = "http://api:8000"
PREDICTION_COST = 5

st.set_page_config(
    page_title="Demand Forecast Dashboard",
    layout="wide"
)
st.markdown("""
<style>

/* Make selectboxes show pointer cursor */
div[data-baseweb="select"] > div {
    cursor: pointer !important;
}

/* Make buttons show pointer cursor */
button {
    cursor: pointer !important;
}

/* Make expanders clickable */
details summary {
    cursor: pointer !important;
}

</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    df = pd.read_csv("model_predictions.csv")
    df["Date"] = pd.to_datetime(df["Date"])
    return df


def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Spring"
    elif month in [6, 7, 8]:
        return "Summer"
    return "Autumn"


def get_balance(headers):
    response = requests.get(f"{API_URL}/balance", headers=headers)
    if response.status_code == 200:
        return response.json()["credits"]
    return 0


def buy_credits(amount, headers):
    return requests.post(
        f"{API_URL}/topup",
        json={"credits": amount},
        headers=headers
    )


df = load_data()


# =========================
# LANGUAGE SELECTOR
# =========================

lang_col1, lang_col2 = st.columns([6, 1])

with lang_col2:
    language = st.selectbox(
        "🌐",
        ["English", "Русский"],
        label_visibility="collapsed"
    )

lang = "ru" if language == "Русский" else "en"
t = TEXT[lang]


def tr(key, fallback):
    return t.get(key, fallback)


# =========================
# SESSION STATE
# =========================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "token" not in st.session_state:
    st.session_state.token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "paid_filter" not in st.session_state:
    st.session_state.paid_filter = None

if "latest_predictions" not in st.session_state:
    st.session_state.latest_predictions = []

if "checkout_bundle" not in st.session_state:
    st.session_state.checkout_bundle = None

if "puzzle_used" not in st.session_state:
    st.session_state.puzzle_used = False


# =========================
# LOGIN
# =========================

st.title(tr("title", "Demand Forecasting Dashboard"))

if not st.session_state.logged_in:
    st.subheader(tr("login", "Login"))

    username = st.text_input(tr("username", "Username"))
    password = st.text_input(tr("password", "Password"), type="password")

    col1, col2 = st.columns(2)

    with col1:
        if st.button(tr("login", "Login")):
            response = requests.post(
                f"{API_URL}/login",
                json={"username": username, "password": password}
            )

            if response.status_code == 200:
                result = response.json()
                st.session_state.logged_in = True
                st.session_state.token = result["token"]
                st.session_state.username = username
                st.rerun()
            else:
                st.error(tr("invalid_login", "Invalid username or password."))

    with col2:
        with st.expander(tr("create_account", "Create account")):
            new_username = st.text_input(tr("new_username", "New username"))
            new_password = st.text_input(tr("new_password", "New password"), type="password")

            if st.button(tr("register", "Register")):
                response = requests.post(
                    f"{API_URL}/register",
                    json={
                        "username": new_username,
                        "password": new_password
                    }
                )

                if response.status_code == 200:
                    st.success(tr("account_created", "Account created. Now login."))
                else:
                    st.error(response.json())

    st.stop()


# =========================
# USER HEADER
# =========================

headers = {"authorization": st.session_state.token}
balance = get_balance(headers)

top1, top2, top3 = st.columns([5, 1, 1])

with top1:
    st.markdown(
        f"""
        <div style="
            padding: 8px 14px;
            border-radius: 10px;
            background-color: rgba(0,255,100,0.08);
            border: 1px solid rgba(0,255,100,0.15);
            display: inline-block;
            font-size: 14px;
            margin-top: 8px;
        ">
            👤 {tr('logged_in', 'Logged in as')} <b>{st.session_state.username}</b>
        </div>
        """,
        unsafe_allow_html=True
    )
with top2:
    st.metric(tr("credits", "Credits"), balance)

with top3:
    if st.button(tr("logout", "Logout")):
        st.session_state.logged_in = False
        st.session_state.token = None
        st.session_state.username = None
        st.session_state.paid_filter = None
        st.session_state.latest_predictions = []
        st.rerun()


# =========================
# FAKE CHECKOUT DIALOG
# =========================

@st.dialog(tr("fake_checkout", "Fake Checkout"))
def checkout_dialog(bundle_amount):
    st.write(f"{tr('buying', 'You are buying')} **{bundle_amount} {tr('credits', 'credits').lower()}**.")
    st.caption(
        tr(
            "checkout_note",
            "This is a simulated checkout for the school project. No real payment is processed."
        )
    )

    cardholder = st.text_input(tr("cardholder", "Cardholder name"))
    last4 = st.text_input(tr("fake_card", "Fake card last 4 digits"), max_chars=4)
    confirm = st.checkbox(tr("confirm_purchase_text", "I confirm this simulated purchase"))

    if st.button(tr("confirm_purchase", "Confirm Purchase")):
        if not cardholder or len(last4) != 4 or not last4.isdigit():
            st.error(tr("checkout_error", "Please enter a cardholder name and 4 fake card digits."))
            return

        if not confirm:
            st.error(tr("confirm_error", "Please confirm the simulated purchase."))
            return

        response = buy_credits(bundle_amount, headers)

        if response.status_code == 200:
            st.success(f"{bundle_amount} {tr('credits_added', 'credits added successfully.')}")
            st.rerun()
        else:
            st.error(tr("checkout_failed", "Could not complete checkout."))


# =========================
# SIDEBAR BILLING
# =========================

st.sidebar.header(tr("credits", "Credits"))
st.sidebar.write(f"{tr('current_balance', 'Current balance')}: **{balance} {tr('credits', 'credits').lower()}**")

with st.sidebar.expander(tr("buy_credits", "Buy Credits")):
    st.write(tr("choose_bundle", "Choose a credit bundle:"))

    col1, col2 = st.columns(2)

    with col1:
        if st.button(f"50 {tr('credits', 'credits').lower()}"):
            checkout_dialog(50)

        if st.button(f"200 {tr('credits', 'credits').lower()}"):
            checkout_dialog(200)

    with col2:
        if st.button(f"100 {tr('credits', 'credits').lower()}"):
            checkout_dialog(100)

        if st.button(f"500 {tr('credits', 'credits').lower()}"):
            checkout_dialog(500)


with st.sidebar.expander(tr("free_puzzle", "Free Credit Puzzle")):
    st.write(tr("solve_puzzle", "Solve the puzzle to get 25 free credits."))

    puzzle_answer = st.number_input(
        tr("puzzle_question", "What is 7 + 8?"),
        min_value=0,
        max_value=100,
        step=1
    )

    if st.button(tr("claim_free", "Claim Free Credits")):
        if st.session_state.puzzle_used:
            st.warning(tr("already_claimed", "You already claimed the free puzzle reward this session."))
        elif puzzle_answer == 15:
            response = buy_credits(25, headers)

            if response.status_code == 200:
                st.session_state.puzzle_used = True
                st.success(tr("correct_puzzle", "Correct. 25 free credits added."))
                st.rerun()
            else:
                st.error(tr("checkout_failed", "Could not complete checkout."))
        else:
            st.error(tr("wrong_puzzle", "Wrong answer. Nice try, future CFO."))


# =========================
# FORECAST SETTINGS
# =========================

st.sidebar.header(tr("forecast_settings", "Forecast Settings"))

all_products = sorted(df["Product_Code"].unique())

selected_products = st.sidebar.multiselect(
    tr("products", "Product(s)"),
    options=all_products,
    default=[all_products[0]],
    help=tr("products_help", "Each product prediction costs credits.")
)

product_filtered = df[df["Product_Code"].isin(selected_products)]

available_categories = sorted(product_filtered["Product_Category"].unique())

selected_categories = st.sidebar.multiselect(
    tr("category", "Category"),
    options=available_categories,
    default=available_categories,
    help=tr("category_help", "Only categories related to selected products appear here.")
)

category_filtered = product_filtered[
    product_filtered["Product_Category"].isin(selected_categories)
]

available_warehouses = sorted(category_filtered["Warehouse"].unique())

selected_warehouses = st.sidebar.multiselect(
    tr("warehouse", "Warehouse"),
    options=available_warehouses,
    default=available_warehouses,
    help=tr("warehouse_help", "Only warehouses containing the selected products appear here.")
)

month = st.sidebar.number_input(
    tr("forecast_month", "Forecast Month"),
    min_value=1,
    max_value=12,
    value=12,
    help=tr("month_help", "Season and quarter are calculated automatically.")
)

year = st.sidebar.number_input(
    tr("forecast_year", "Forecast Year"),
    min_value=2011,
    max_value=2030,
    value=2017
)

quarter = ((month - 1) // 3) + 1
season = get_season(month)
is_holiday_season = 1 if month in [11, 12] else 0

st.sidebar.caption(f"{tr('auto_calculated', 'Auto-calculated')}: {season}, Q{quarter}")

selection_df = category_filtered[
    category_filtered["Warehouse"].isin(selected_warehouses)
].copy()

if selection_df.empty:
    st.warning(tr("no_selection", "No data available for this selection."))
    st.stop()

prediction_combinations = (
    selection_df[["Product_Code", "Warehouse", "Product_Category"]]
    .drop_duplicates()
)

total_cost = len(prediction_combinations) * PREDICTION_COST

st.sidebar.info(
    f"{tr('request_cost', 'This request will run')} "
    f"{len(prediction_combinations)} "
    f"{tr('predictions_and_cost', 'prediction(s) and cost')} "
    f"{total_cost} {tr('credits', 'credits').lower()}."
)


# =========================
# ADVANCED OPTIONS
# =========================

with st.sidebar.expander(tr("advanced_options", "Advanced options")):
    st.caption(
        tr(
            "advanced_caption",
            "These values are auto-filled from recent history. Change only for scenario testing."
        )
    )

    latest_row = selection_df.sort_values("Date").iloc[-1]

    lag_1 = st.number_input(
        tr("lag_1", "Lag 1"),
        value=float(latest_row["Actual_Demand"]),
        help=tr("lag_1_help", "Previous month demand. Higher values tell the model recent demand is stronger.")
    )

    lag_2 = st.number_input(
        tr("lag_2", "Lag 2"),
        value=float(latest_row["Baseline_Prediction"]),
        help=tr("lag_2_help", "Demand from two periods ago. Helps detect short-term movement.")
    )

    lag_3 = st.number_input(
        tr("lag_3", "Lag 3"),
        value=float(latest_row["Predicted_Demand"]),
        help=tr("lag_3_help", "Demand from three periods ago. Helps detect repeated demand behavior.")
    )

    lag_6 = st.number_input(
        tr("lag_6", "Lag 6"),
        value=float(latest_row["Actual_Demand"]),
        help=tr("lag_6_help", "Demand from six periods ago. Helps capture longer patterns.")
    )

    rolling_mean_3 = st.number_input(
        tr("rolling_mean_3", "Rolling Mean 3"),
        value=float(selection_df["Actual_Demand"].tail(3).mean()),
        help=tr("rolling_mean_3_help", "Average demand over the last 3 periods. Smooths short-term spikes.")
    )

    rolling_mean_6 = st.number_input(
        tr("rolling_mean_6", "Rolling Mean 6"),
        value=float(selection_df["Actual_Demand"].tail(6).mean()),
        help=tr("rolling_mean_6_help", "Average demand over the last 6 periods. Smooths longer demand trends.")
    )

    unit_price_override = st.number_input(
        tr("unit_price", "Unit Price"),
        value=float(latest_row["Unit_Price"]),
        help=tr(
            "unit_price_help",
            "Scenario price used for revenue. Since price is simulated, changing it mainly changes revenue."
        )
    )


run_prediction = st.sidebar.button(tr("run_prediction", "Run Paid Prediction"))


# =========================
# RUN PAID PREDICTIONS
# =========================

if run_prediction:
    current_balance = get_balance(headers)

    if current_balance < total_cost:
        st.error(
            f"{tr('insufficient', 'Insufficient credits.')} "
            f"{tr('need', 'You need')} {total_cost} {tr('credits', 'credits').lower()}, "
            f"{tr('but_have', 'but you only have')} {current_balance}."
        )

        st.warning(tr("buy_more_sidebar", "Buy more credits from the sidebar to continue."))

    else:
        prediction_results = []

        for _, row in prediction_combinations.iterrows():
            product = row["Product_Code"]
            warehouse = row["Warehouse"]
            category = row["Product_Category"]

            product_history = selection_df[
                (selection_df["Product_Code"] == product) &
                (selection_df["Warehouse"] == warehouse)
            ].sort_values("Date")

            if product_history.empty:
                continue

            payload = {
                "Product_Code": product,
                "Warehouse": warehouse,
                "Product_Category": category,
                "season": season,
                "month": month,
                "quarter": quarter,
                "year": year,
                "is_holiday_season": is_holiday_season,
                "lag_1": lag_1,
                "lag_2": lag_2,
                "lag_3": lag_3,
                "lag_6": lag_6,
                "rolling_mean_3": rolling_mean_3,
                "rolling_mean_6": rolling_mean_6,
                "Unit_Price": unit_price_override
            }

            response = requests.post(
                f"{API_URL}/predict",
                json=payload,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                result["Product_Code"] = product
                result["Warehouse"] = warehouse
                result["Product_Category"] = category
                prediction_results.append(result)
            else:
                st.error(tr("prediction_failed", "Prediction failed for one item."))
                st.error(response.json())

        st.session_state.latest_predictions = prediction_results

        st.session_state.paid_filter = {
            "products": selected_products,
            "categories": selected_categories,
            "warehouses": selected_warehouses
        }

        st.success(tr("prediction_completed", "Paid prediction completed."))
        st.rerun()


# =========================
# MAIN RESULTS
# =========================

if st.session_state.paid_filter is None:
    st.info(tr("no_prediction", "Choose products and run a paid prediction to view results and graphs."))
    st.stop()


paid_filter = st.session_state.paid_filter

filtered = df[
    (df["Product_Code"].isin(paid_filter["products"])) &
    (df["Product_Category"].isin(paid_filter["categories"])) &
    (df["Warehouse"].isin(paid_filter["warehouses"]))
].copy()

if filtered.empty:
    st.warning(tr("no_historical", "No saved historical data for the paid selection."))
    st.stop()


st.header(tr("paid_results", "Paid Forecast Results"))

if st.session_state.latest_predictions:
    latest_df = pd.DataFrame(st.session_state.latest_predictions)

    total_predicted_demand = latest_df["predicted_demand"].sum()
    total_predicted_revenue = latest_df["predicted_revenue"].sum()
    remaining_credits = latest_df["remaining_credits"].iloc[-1]

    r1, r2, r3 = st.columns(3)

    r1.metric(tr("new_predicted_demand", "New Predicted Demand"), f"{total_predicted_demand:,.0f}")
    r2.metric(tr("new_predicted_revenue", "New Predicted Revenue"), f"${total_predicted_revenue:,.0f}")
    r3.metric(tr("remaining_credits", "Remaining Credits"), remaining_credits)

    with st.expander(tr("view_latest", "View latest paid prediction details")):
        st.dataframe(latest_df)


# =========================
# METRICS
# =========================

st.header(tr("historical_performance", "Historical Performance for Paid Selection"))

mae = mean_absolute_error(
    filtered["Actual_Demand"],
    filtered["Predicted_Demand"]
)

rmse = np.sqrt(
    mean_squared_error(
        filtered["Actual_Demand"],
        filtered["Predicted_Demand"]
    )
)

baseline_mae = mean_absolute_error(
    filtered["Actual_Demand"],
    filtered["Baseline_Prediction"]
)

total_actual_revenue = filtered["Revenue"].sum()
total_predicted_revenue = filtered["Predicted_Revenue"].sum()

m1, m2, m3, m4 = st.columns(4)

m1.metric(tr("model_mae", "Model MAE"), f"{mae:,.0f}")
m2.metric(tr("model_rmse", "Model RMSE"), f"{rmse:,.0f}")
m3.metric(tr("baseline_mae", "Baseline MAE"), f"{baseline_mae:,.0f}")
m4.metric(tr("mae_improvement", "MAE Improvement"), f"{baseline_mae - mae:,.0f}")

m5, m6 = st.columns(2)

m5.metric(tr("actual_revenue", "Actual Revenue"), f"${total_actual_revenue:,.0f}")
m6.metric(tr("predicted_revenue", "Predicted Revenue"), f"${total_predicted_revenue:,.0f}")


# =========================
# CHARTS
# =========================

st.subheader(tr("demand_over_time", "Demand Over Time"))

demand_over_time = (
    filtered.groupby("Date", as_index=False)[
        ["Actual_Demand", "Predicted_Demand", "Baseline_Prediction"]
    ]
    .sum()
)

st.line_chart(
    demand_over_time,
    x="Date",
    y=["Actual_Demand", "Predicted_Demand", "Baseline_Prediction"]
)

st.subheader(tr("revenue_over_time", "Revenue Over Time"))

revenue_over_time = (
    filtered.groupby("Date", as_index=False)[
        ["Revenue", "Predicted_Revenue"]
    ]
    .sum()
)

st.line_chart(
    revenue_over_time,
    x="Date",
    y=["Revenue", "Predicted_Revenue"]
)

st.subheader(tr("prediction_error", "Prediction Error Over Time"))

filtered["Prediction_Error"] = (
    filtered["Actual_Demand"] - filtered["Predicted_Demand"]
)

error_over_time = (
    filtered.groupby("Date", as_index=False)["Prediction_Error"]
    .mean()
)

st.line_chart(
    error_over_time,
    x="Date",
    y="Prediction_Error"
)


# =========================
# TRANSACTIONS
# =========================

with st.expander(tr("transactions", "Billing Transactions")):
    tx_response = requests.get(
        f"{API_URL}/transactions",
        headers=headers
    )

    if tx_response.status_code == 200:
        transactions = tx_response.json()["transactions"]
        st.dataframe(pd.DataFrame(transactions))
    else:
        st.error(tr("transactions_failed", "Could not load transactions."))


with st.expander(tr("selected_data", "View historical data for paid selection")):
    st.dataframe(filtered)