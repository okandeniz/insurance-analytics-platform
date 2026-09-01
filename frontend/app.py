import random
from datetime import date, timedelta

import requests
import streamlit as st


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="Insurance Analytics Platform",
    page_icon="📊",
    layout="wide",
)


BACKEND_URL = "http://127.0.0.1:8000/predict"


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .stApp {
        background: linear-gradient(
            180deg,
            #07111f 0%,
            #0a1628 100%
        );
        color: #f5f7fa;
    }

    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    .hero-card {
        background: linear-gradient(
            135deg,
            rgba(13,110,253,0.18),
            rgba(25,135,84,0.18)
        );

        border: 1px solid rgba(255,255,255,0.08);

        padding: 28px 30px;

        border-radius: 20px;

        margin-bottom: 1.2rem;

        box-shadow:
            0 8px 24px rgba(0,0,0,0.25);
    }

    .hero-title {
        font-size: 2.4rem;
        font-weight: 800;
        margin-bottom: 0.2rem;
        color: white;
    }

    .hero-subtitle {
        font-size: 1.05rem;
        color: #cfd8e3;
        margin-bottom: 1rem;
    }

    .badge-wrap {
        display: flex;
        gap: 10px;
        flex-wrap: wrap;
        margin-top: 8px;
    }

    .badge {
        background-color:
            rgba(255,255,255,0.08);

        color: #e9eef5;

        border:
            1px solid rgba(255,255,255,0.08);

        padding: 6px 12px;

        border-radius: 999px;

        font-size: 0.85rem;
    }

    .section-card {
        background:
            rgba(255,255,255,0.04);

        border:
            1px solid rgba(255,255,255,0.08);

        border-radius: 18px;

        padding:
            20px 20px 8px 20px;

        margin-bottom: 1rem;

        box-shadow:
            0 6px 18px rgba(0,0,0,0.18);
    }

    .section-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: white;
    }

    .result-card {
        background: linear-gradient(
            135deg,
            rgba(25,135,84,0.18),
            rgba(32,201,151,0.12)
        );

        border:
            1px solid rgba(32,201,151,0.25);

        border-radius: 20px;

        padding: 24px;

        margin-top: 1rem;

        box-shadow:
            0 8px 24px rgba(0,0,0,0.25);
    }

    .result-label {
        font-size: 1rem;
        color: #cfd8e3;
        margin-bottom: 0.5rem;
    }

    .result-value {
        font-size: 2.4rem;
        font-weight: 800;
        color: #ffffff;
    }

    .helper-text {
        color: #b8c2cc;
        font-size: 0.92rem;
    }

    .small-note {
        font-size: 0.85rem;
        color: #aab4be;
    }

    div.stButton > button,
    div[data-testid="stFormSubmitButton"] > button {

        width: 100%;
        height: 3.2rem;

        border-radius: 14px;
        border: none;

        background:
            linear-gradient(
                90deg,
                #198754,
                #20c997
            );

        color: white;

        font-size: 1rem;
        font-weight: 700;

        box-shadow:
            0 8px 18px
            rgba(25,135,84,0.30);
    }

    div.stButton > button:hover,
    div[data-testid="stFormSubmitButton"] > button:hover {

        filter: brightness(1.06);

        transform:
            translateY(-1px);
    }

    [data-testid="stSidebar"] {
        background:
            rgba(255,255,255,0.03);

        border-right:
            1px solid rgba(255,255,255,0.06);
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.title("📌 About")

    st.markdown(
        """
        This application estimates
        **post-claim damage severity**
        using a trained machine learning model.

        **Use case**
        - Post-claim triage
        - Reserve support
        - Early severity estimation

        **Model**
        - Random Forest
        - Log target strategy
        """
    )

    st.info(
        "Make sure the backend is running on "
        "`http://127.0.0.1:8000`."
    )


# -----------------------------
# HERO SECTION
# -----------------------------

hero_html = """
<div class="hero-card">
    <div class="hero-title">
        Insurance Analytics Platform
    </div>

    <div class="hero-subtitle">
        Estimate the expected damage amount
        after an insurance claim has been reported.
    </div>

    <div class="badge-wrap">
        <div class="badge">
            Claim Severity Estimator
        </div>

        <div class="badge">
            Post-Claim Triage
        </div>

        <div class="badge">
            Reserve Support
        </div>
    </div>
</div>
"""

st.html(hero_html)


# ============================================================
# OPTIONS
# ============================================================

CLAIM_TYPES = [
    "Theft",
    "Collision",
    "Fire",
    "Vandalism",
    "Glass_damage",
]

GENDERS = [
    "Male",
    "Female",
]

CUSTOMER_SEGMENTS = [
    "Manager",
    "Employee",
    "Worker",
    "Self_employed",
    "Retired",
    "Student",
    "Unemployed",
]

CHANNELS = [
    "Broker",
    "Agency",
    "Web",
    "Phone",
]

RISK_ZONES = [
    "Low",
    "Medium",
    "High",
]

BRANDS = [
    "Volkswagen",
    "Peugeot",
    "Renault",
    "BMW",
    "Mercedes",
]

FUEL_TYPES = [
    "Diesel",
    "Gasoline",
    "Electric",
    "Hybrid",
]

VEHICLE_USAGES = [
    "Personal",
    "Professional",
    "Mixed",
]


# ============================================================
# DEFAULT DATA
# ============================================================

DEFAULT_DATA = {

    "occurrence_date":
        date.today(),

    "claim_type":
        "Theft",

    "declaration_lag_days":
        0.0,

    "previous_claims":
        0,

    "client_age":
        39.0,

    "gender":
        "Male",

    "csp":
        "Manager",

    "channel":
        "Broker",

    "risk_zone":
        "Low",

    "annual_premium":
        628.54,

    "brand":
        "Volkswagen",

    "vehicle_usage":
        "Personal",

    "vehicle_age_at_claim":
        1.0,

    "fuel_type":
        "Diesel",

    "power_hp":
        134.1,

    "current_value":
        13520.60,
}


for key, value in DEFAULT_DATA.items():

    if key not in st.session_state:

        st.session_state[key] = value


# ============================================================
# RANDOM DATA
# ============================================================

def generate_random_data() -> None:

    start_date = date(
        2023,
        1,
        1,
    )

    end_date = date(
        2025,
        10,
        20,
    )

    days_between = (
        end_date
        - start_date
    ).days

    st.session_state[
        "occurrence_date"
    ] = (
        start_date
        + timedelta(
            days=random.randint(
                0,
                days_between,
            )
        )
    )

    st.session_state[
        "claim_type"
    ] = random.choice(
        CLAIM_TYPES
    )

    st.session_state[
        "declaration_lag_days"
    ] = float(
        random.randint(
            0,
            90,
        )
    )

    st.session_state[
        "previous_claims"
    ] = random.randint(
        0,
        3,
    )

    st.session_state[
        "client_age"
    ] = float(
        random.randint(
            18,
            75,
        )
    )

    st.session_state[
        "gender"
    ] = random.choice(
        GENDERS
    )

    st.session_state[
        "csp"
    ] = random.choice(
        CUSTOMER_SEGMENTS
    )

    st.session_state[
        "channel"
    ] = random.choice(
        CHANNELS
    )

    st.session_state[
        "risk_zone"
    ] = random.choice(
        RISK_ZONES
    )

    st.session_state[
        "annual_premium"
    ] = round(
        random.uniform(
            300,
            1500,
        ),
        2,
    )

    st.session_state[
        "brand"
    ] = random.choice(
        BRANDS
    )

    st.session_state[
        "fuel_type"
    ] = random.choice(
        FUEL_TYPES
    )

    st.session_state[
        "vehicle_usage"
    ] = random.choice(
        VEHICLE_USAGES
    )

    st.session_state[
        "power_hp"
    ] = round(
        random.uniform(
            70,
            250,
        ),
        1,
    )

    st.session_state[
        "vehicle_age_at_claim"
    ] = float(
        random.randint(
            0,
            14,
        )
    )

    st.session_state[
        "current_value"
    ] = round(
        random.uniform(
            5000,
            50000,
        ),
        2,
    )


# ============================================================
# RANDOM DATA BUTTON
# ============================================================

button_col1, button_col2 = st.columns(
    [1.25, 4]
)


with button_col1:

    st.button(
        "🎲 Random Data",
        on_click=generate_random_data,
        use_container_width=True,
    )


# ============================================================
# FORM
# ============================================================

with st.form(
    "claim_form",
):

    # ========================================================
    # CLAIM INFORMATION
    # ========================================================

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Claim Information'
        '</div>',
        unsafe_allow_html=True,
    )


    c1, c2 = st.columns(
        2
    )


    with c1:

        occurrence_date = st.date_input(
            "Occurrence Date",
            key="occurrence_date",
        )

        claim_type = st.selectbox(
            "Claim Type",
            CLAIM_TYPES,
            key="claim_type",
        )


    with c2:

        declaration_lag_days = st.number_input(
            "Declaration Lag (Days)",
            min_value=0.0,
            step=1.0,
            key="declaration_lag_days",
        )

        previous_claims = st.number_input(
            "Previous Claims",
            min_value=0,
            step=1,
            key="previous_claims",
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # ========================================================
    # CUSTOMER INFORMATION
    # ========================================================

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Customer Information'
        '</div>',
        unsafe_allow_html=True,
    )


    c1, c2, c3 = st.columns(
        3
    )


    with c1:

        client_age = st.number_input(
            "Client Age",
            min_value=18.0,
            max_value=100.0,
            step=1.0,
            key="client_age",
        )

        gender = st.selectbox(
            "Gender",
            GENDERS,
            key="gender",
        )


    with c2:

        csp = st.selectbox(
            "Customer Segment",
            CUSTOMER_SEGMENTS,
            key="csp",
        )

        channel = st.selectbox(
            "Channel",
            CHANNELS,
            key="channel",
        )


    with c3:

        risk_zone = st.selectbox(
            "Risk Zone",
            RISK_ZONES,
            key="risk_zone",
        )

        annual_premium = st.number_input(
            "Annual Premium",
            min_value=0.01,
            step=10.0,
            format="%.2f",
            key="annual_premium",
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    # ========================================================
    # VEHICLE INFORMATION
    # ========================================================

    st.markdown(
        '<div class="section-card">',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="section-title">'
        'Vehicle Information'
        '</div>',
        unsafe_allow_html=True,
    )


    c1, c2, c3 = st.columns(
        3
    )


    with c1:

        brand = st.selectbox(
            "Brand",
            BRANDS,
            key="brand",
        )

        fuel_type = st.selectbox(
            "Fuel Type",
            FUEL_TYPES,
            key="fuel_type",
        )


    with c2:

        vehicle_usage = st.selectbox(
            "Vehicle Usage",
            VEHICLE_USAGES,
            key="vehicle_usage",
        )

        power_hp = st.number_input(
            "Power (HP)",
            min_value=0.1,
            step=1.0,
            format="%.1f",
            key="power_hp",
        )


    with c3:

        vehicle_age_at_claim = (
            st.number_input(
                "Vehicle Age",
                min_value=0.0,
                step=1.0,
                key="vehicle_age_at_claim",
            )
        )

        current_value = st.number_input(
            "Current Vehicle Value",
            min_value=0.01,
            step=100.0,
            format="%.2f",
            key="current_value",
        )


    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


    submitted = (
        st.form_submit_button(
            "Estimate Damage",
            use_container_width=True,
        )
    )


# ============================================================
# PREDICTION
# ============================================================

if submitted:

    payload = {

        "occurrence_date":
            occurrence_date.isoformat(),

        "claim_type":
            claim_type,

        "risk_zone":
            risk_zone,

        "channel":
            channel,

        "csp":
            csp,

        "gender":
            gender,

        "brand":
            brand,

        "fuel_type":
            fuel_type,

        "vehicle_usage":
            vehicle_usage,

        "annual_premium":
            float(
                annual_premium
            ),

        "client_age":
            float(
                client_age
            ),

        "power_hp":
            float(
                power_hp
            ),

        "vehicle_age_at_claim":
            float(
                vehicle_age_at_claim
            ),

        "current_value":
            float(
                current_value
            ),

        "previous_claims":
            int(
                previous_claims
            ),

        "declaration_lag_days":
            float(
                declaration_lag_days
            ),
    }


    try:

        with st.spinner(
            "Prediction is running..."
        ):

            response = requests.post(
                BACKEND_URL,
                json=payload,
                timeout=30,
            )


        if response.status_code == 200:

            result = response.json()

            prediction = result[
                "predicted_damage_amount"
            ]


            st.success(
                "Prediction completed successfully."
            )


            result_html = f"""
            <div class="result-card">

                <div class="result-label">
                    Estimated Claim Severity
                </div>

                <div class="result-value">
                    {prediction:,.2f}
                </div>

                <br>

                <div class="helper-text">
                    This estimate is intended for
                    post-claim triage and reserve support.
                </div>

                <br>

                <div class="small-note">
                    Model: {result.get("model_name", "N/A")}
                    <br>
                    Usage: {result.get("usage", "N/A")}
                </div>

            </div>
            """

            st.html(result_html)


        else:

            st.error(
                f"API Error: "
                f"{response.status_code}"
            )

            st.json(
                response.json()
            )


    except requests.RequestException as exc:

        st.error(
            "Could not connect to the backend API."
        )

        st.caption(
            str(exc)
        )