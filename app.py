import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px
import os

# --------------------------------------------------
# PAGE CONFIG
# --------------------------------------------------
st.set_page_config(
    page_title="FitInsight AI",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM CSS (COLORFUL + MODERN)
# --------------------------------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background-color: #F8FAFC;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A, #020617);
    padding-top: 20px;
}

/* Sidebar text */
section[data-testid="stSidebar"] * {
    color: white !important;
}

/* KPI Cards */
.kpi-card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 6px 18px rgba(0,0,0,0.08);
    text-align: center;
}
.kpi-card h2 {
    color: #7C3AED;
}

/* Section titles */
.section-title {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 8px;
}
.section-sub {
    color: #6B7280;
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# DATABASE (LOGIN)
# --------------------------------------------------
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE,
    password BLOB
)
""")
conn.commit()

# --------------------------------------------------
# AUTH HELPERS
# --------------------------------------------------
def hash_password(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def verify_password(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed)

# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# --------------------------------------------------
# LOGIN PAGE
# --------------------------------------------------
if not st.session_state.logged_in:
    st.title("🔐 FitInsight AI Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        cursor.execute("SELECT password FROM users WHERE email=?", (email,))
        result = cursor.fetchone()
        if result and verify_password(password, result[0]):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Invalid email or password")

    if col2.button("Sign Up"):
        try:
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hash_password(password))
            )
            conn.commit()
            st.success("Account created. Please login.")
        except:
            st.error("User already exists")

    st.stop()

# --------------------------------------------------
# SIDEBAR (SAFE LOGO HANDLING)
# --------------------------------------------------
if os.path.exists("logo.png"):
    st.sidebar.image("logo.png", width=120)
else:
    st.sidebar.markdown("## 🏋️ FitInsight AI")

st.sidebar.markdown(f"👤 **{st.session_state.email}**")
st.sidebar.markdown("---")

if st.sidebar.button("📊 Overview"):
    st.session_state.page = "Overview"
if st.sidebar.button("📈 Analytics"):
    st.session_state.page = "Analytics"
if st.sidebar.button("⚠️ Risk & Churn"):
    st.session_state.page = "Risk"
if st.sidebar.button("📂 Data Explorer"):
    st.session_state.page = "Data"

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged_in = False
    st.rerun()

# --------------------------------------------------
# DATA UPLOAD
# --------------------------------------------------
st.info("🔐 Data Privacy: Files are processed in memory only. No data is stored.")

uploaded_file = st.file_uploader(
    "Upload Gym Data (CSV or Excel)",
    type=["csv", "xlsx"]
)

if not uploaded_file:
    st.stop()

# --------------------------------------------------
# LOAD + CLEAN DATA
# --------------------------------------------------
df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

# Auto-detect member_id
for col in df.columns:
    if col.replace("_", "") in ["memberid", "customerid", "userid", "id"]:
        df.rename(columns={col: "member_id"}, inplace=True)

if "member_id" not in df.columns:
    st.error("❌ No member ID column found")
    st.stop()

# Normalize status
if "status" not in df.columns:
    df["status"] = "inactive"

df["status"] = df["status"].astype(str).str.lower().map({
    "active": "Active",
    "inactive": "Inactive",
    "yes": "Active",
    "no": "Inactive",
    "1": "Active",
    "0": "Inactive",
    "true": "Active",
    "false": "Inactive"
}).fillna("Inactive")

# Revenue column
if "amount" not in df.columns:
    df["amount"] = 0
else:
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# --------------------------------------------------
# KPIs
# --------------------------------------------------
total_members = df["member_id"].nunique()
active_members = df[df["status"] == "Active"]["member_id"].nunique()
inactive_members = total_members - active_members
total_revenue = df["amount"].sum()
avg_revenue = round(total_revenue / total_members, 2) if total_members else 0

# --------------------------------------------------
# OVERVIEW PAGE
# --------------------------------------------------
if st.session_state.page == "Overview":
    st.markdown('<div class="section-title">📊 Business Overview</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-sub">Key gym performance metrics</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"<div class='kpi-card'><h4>Total Members</h4><h2>{total_members}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='kpi-card'><h4>Active Members</h4><h2>{active_members}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='kpi-card'><h4>Inactive Members</h4><h2>{inactive_members}</h2></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='kpi-card'><h4>Total Revenue</h4><h2>₹{total_revenue}</h2></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        fig = px.pie(df, names="status", hole=0.45, title="Active vs Inactive Members")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.bar(
            df["status"].value_counts().reset_index(),
            x="index",
            y="status",
            labels={"index": "Status", "status": "Count"},
            title="Member Status Count"
        )
        st.plotly_chart(fig2, use_container_width=True)

# --------------------------------------------------
# ANALYTICS PAGE
# --------------------------------------------------
elif st.session_state.page == "Analytics":
    st.markdown('<div class="section-title">📈 Analytics</div>', unsafe_allow_html=True)

    fig = px.histogram(
        df,
        x="status",
        color="status",
        title="Member Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# --------------------------------------------------
# RISK PAGE
# --------------------------------------------------
elif st.session_state.page == "Risk":
    st.markdown('<div class="section-title">⚠️ Risk & Churn Analysis</div>', unsafe_allow_html=True)

    df["risk_level"] = df["status"].apply(
        lambda x: "High Risk" if x == "Inactive" else "Low Risk"
    )

    fig = px.bar(
        df["risk_level"].value_counts().reset_index(),
        x="index",
        y="risk_level",
        title="Risk Distribution",
        color="index"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(df[["member_id", "status", "risk_level"]])

# --------------------------------------------------
# RAW DATA
# --------------------------------------------------
elif st.session_state.page == "Data":
    st.markdown('<div class="section-title">📂 Raw Data</div>', unsafe_allow_html=True)
    st.dataframe(df)
