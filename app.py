"""
Streamlit frontend for the California House Price Prediction API.

Run with:
    streamlit run app.py

Make sure the FastAPI backend (main.py) is running first, e.g.:
    uvicorn main:app --reload
"""

import io
import requests
import pandas as pd
import streamlit as st

# --------------------------------------------------------------------------
# Page configuration
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="California House Price Predictor",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --------------------------------------------------------------------------
# Styling
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        html, body, [class*="css"] {
            font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }

        .main-header {
            font-size: 2.1rem;
            font-weight: 700;
            color: #1a1a2e;
            margin-bottom: 0.1rem;
        }
        .sub-header {
            font-size: 1rem;
            color: #6b7280;
            margin-bottom: 1.6rem;
        }

        .metric-card {
            background: linear-gradient(135deg, #16213e 0%, #0f3460 100%);
            padding: 1.4rem 1.6rem;
            border-radius: 14px;
            color: white;
            text-align: center;
            box-shadow: 0 4px 14px rgba(15, 52, 96, 0.25);
        }
        .metric-card .label {
            font-size: 0.85rem;
            opacity: 0.75;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }
        .metric-card .value {
            font-size: 2rem;
            font-weight: 700;
            margin-top: 0.3rem;
        }
        .metric-card .range {
            font-size: 0.85rem;
            opacity: 0.85;
            margin-top: 0.4rem;
        }

        .status-pill {
            display: inline-block;
            padding: 0.25rem 0.7rem;
            border-radius: 999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .status-online {
            background-color: #dcfce7;
            color: #166534;
        }
        .status-offline {
            background-color: #fee2e2;
            color: #991b1b;
        }

        section[data-testid="stSidebar"] {
            background-color: #f8fafc;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 6px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px 8px 0 0;
            padding: 0.5rem 1.1rem;
        }

        footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar — API configuration & health
# --------------------------------------------------------------------------
API_BASE_URL = "https://housing-fastapi-1.onrender.com"

with st.sidebar:
    st.markdown("### 📡 API Status")

    health_data = None
    try:
        resp = requests.get(f"{API_BASE_URL}/health", timeout=60)
        if resp.status_code == 200:
            health_data = resp.json()
            st.markdown(
                '<span class="status-pill status-online">● Online</span>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<span class="status-pill status-offline">● Error</span>',
                unsafe_allow_html=True,
            )
    except requests.exceptions.RequestException:
        st.markdown(
            '<span class="status-pill status-offline">● Waking up / Offline</span>',
            unsafe_allow_html=True,
        )

    if health_data:
        st.caption(f"Model: **{health_data.get('model', 'n/a')}**")
        st.caption(f"Avg. error: **{health_data.get('avg_error', 'n/a')}**")

    st.markdown("---")
    st.caption(
        "⏳ First request after inactivity can take 30–60s while the "
        "free-tier backend wakes up."
    )
    st.caption("California Housing • RandomForestRegressor")

# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------
st.markdown('<div class="main-header">🏠 California House Price Predictor</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Estimate median house values from California census-tract features, '
    "one home at a time or in bulk via CSV.</div>",
    unsafe_allow_html=True,
)

tab_single, tab_batch, tab_about = st.tabs(["🔍 Single Prediction", "📂 Batch Prediction", "ℹ️ About"])

# --------------------------------------------------------------------------
# Tab 1 — Single prediction
# --------------------------------------------------------------------------
with tab_single:
    st.markdown("#### Enter tract features")

    col1, col2 = st.columns(2)
    with col1:
        med_inc = st.number_input(
            "Median income (in $10,000s)", min_value=0.1, max_value=20.0, value=5.0, step=0.1,
            help="e.g. 5.0 represents a median income of $50,000."
        )
        house_age = st.number_input("Median house age (years)", min_value=0.0, max_value=60.0, value=25.0, step=1.0)
        ave_rooms = st.number_input("Average rooms per household", min_value=0.5, max_value=20.0, value=5.5, step=0.1)
        ave_bedrms = st.number_input("Average bedrooms per household", min_value=0.1, max_value=10.0, value=1.1, step=0.1)
    with col2:
        population = st.number_input("Tract population", min_value=1.0, max_value=40000.0, value=1200.0, step=10.0)
        ave_occup = st.number_input("Average occupants per household", min_value=0.1, max_value=20.0, value=3.0, step=0.1)
        latitude = st.slider("Latitude", min_value=32.0, max_value=42.0, value=36.5, step=0.01)
        longitude = st.slider("Longitude", min_value=-125.0, max_value=-114.0, value=-119.5, step=0.01)

    st.markdown("")
    predict_clicked = st.button("Predict price", type="primary", use_container_width=True)

    if predict_clicked:
        payload = {
            "MedInc": med_inc,
            "HouseAge": house_age,
            "AveRooms": ave_rooms,
            "AveBedrms": ave_bedrms,
            "Population": population,
            "AveOccup": ave_occup,
            "Latitude": latitude,
            "Longitude": longitude,
        }
        try:
            with st.spinner("Contacting model... (first request after inactivity can take up to a minute)"):
                r = requests.post(f"{API_BASE_URL}/predict", json=payload, timeout=60)
            if r.status_code == 200:
                result = r.json()
                st.markdown("")
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="label">Predicted price</div>
                        <div class="value">{result.get('predicted_price', 'N/A')}</div>
                        <div class="range">Confidence range: {result.get('fidence_range', 'N/A')}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                try:
                    detail = r.json().get("detail", r.text)
                except ValueError:
                    detail = r.text
                st.error(f"API error ({r.status_code}): {detail}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach the API at {API_BASE_URL}. Details: {e}")

# --------------------------------------------------------------------------
# Tab 2 — Batch prediction
# --------------------------------------------------------------------------
with tab_batch:
    st.markdown("#### Upload a CSV for bulk predictions")
    st.caption(
        "Required columns: `MedInc`, `HouseAge`, `AveRooms`, `AveBedrms`, "
        "`Population`, `AveOccup`, `Latitude`, `Longitude`"
    )

    uploaded_file = st.file_uploader("Choose a CSV file", type=["csv"])

    if uploaded_file is not None:
        try:
            preview_df = pd.read_csv(uploaded_file)
            st.markdown("**Preview**")
            st.dataframe(preview_df.head(10), use_container_width=True)
            st.caption(f"{len(preview_df)} rows detected.")
            uploaded_file.seek(0)
        except Exception as e:
            st.error(f"Could not read this file as CSV: {e}")
            preview_df = None

        run_clicked = st.button("Run batch prediction", type="primary", use_container_width=True)

        if run_clicked:
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}
                with st.spinner("Scoring file... (first request after inactivity can take up to a minute)"):
                    r = requests.post(f"{API_BASE_URL}/predict-file", files=files, timeout=90)

                if r.status_code == 200:
                    result_df = pd.read_csv(io.StringIO(r.content.decode("utf-8")))
                    st.success(f"Predicted prices for {len(result_df)} rows.")
                    st.dataframe(result_df, use_container_width=True)

                    st.download_button(
                        label="⬇️ Download predictions.csv",
                        data=r.content,
                        file_name="predictions.csv",
                        mime="text/csv",
                        use_container_width=True,
                    )
                else:
                    try:
                        detail = r.json().get("detail", r.text)
                    except ValueError:
                        detail = r.text
                    st.error(f"API error ({r.status_code}): {detail}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach the API at {API_BASE_URL}. Details: {e}")

# --------------------------------------------------------------------------
# Tab 3 — About
# --------------------------------------------------------------------------
with tab_about:
    st.markdown("#### About this app")
    st.write(
        "This interface talks to a FastAPI service that serves a `RandomForestRegressor` "
        "trained on the scikit-learn California Housing dataset. It exposes two endpoints:"
    )
    st.markdown(
        """
        - **`POST /predict`** — predicts the price for a single home from its features.
        - **`POST /predict-file`** — accepts a CSV of homes and returns a CSV with an
          added `predicted_columns_usd` column.
        """
    )
    st.markdown("#### Feature reference")
    ref_df = pd.DataFrame(
        {
            "Feature": ["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude"],
            "Description": [
                "Median income in the block group (tens of thousands of $)",
                "Median house age in the block group (years)",
                "Average number of rooms per household",
                "Average number of bedrooms per household",
                "Total population in the block group",
                "Average number of household members",
                "Block group latitude",
                "Block group longitude",
            ],
        }
    )
    st.dataframe(ref_df, use_container_width=True, hide_index=True)

    st.markdown("#### Running locally")
    st.code(
        "# Terminal 1 — start the API\n"
        "uvicorn main:app --reload\n\n"
        "# Terminal 2 — start this UI\n"
        "streamlit run app.py",
        language="bash",
    )