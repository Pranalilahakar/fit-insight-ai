import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px

# ---------------- PAGE CONFIG ----------------
st.set_page_config(page_title="FitInsight AI", layout="wide")

# ---------------- DATABASE (AUTH) ----------------
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

# ---------------- AUTH FUNCTIONS ----------------
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def signup(email, password):
    try:
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hash_password(password))
        )
        conn.commit()
        return True
    except:
        return False

def login(email, password):
    cursor.execute("SELECT password FROM users WHERE email=?", (email,))
    result = cursor.fetchone()
    if result and verify_password(password, result[0]):
        return True
    return False

# ---------------- SESSION ----------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "email" not in st.session_state:
    st.session_state.email = ""

# ---------------- LOGIN UI ----------------
if not st.session_state.logged_in:
    st.title("🔐 FitInsight AI – Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        if login(email, password):
            st.session_state.logged_in = True
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Invalid credentials")

    if col2.button("Sign Up"):
        if signup(email, password):
            st.success("Account created. Please login.")
        else:
            st.error("User already exists")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.title("🏋️ FitInsight AI")
st.sidebar.write(st.session_state.email)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🏃 Attendance", "⚠️ Risk Analysis", "📂 Raw Data"]
)

# ---------------- DATA PRIVACY NOTICE ----------------
st.info(
    "🔐 **Data Privacy Notice**: "
    "Your data is processed temporarily in memory. "
    "No files are stored. No third-party sharing."
)

# ---------------- FILE UPLOAD ----------------
uploaded_file = st.file_uploader(
    "Upload Gym Data (Excel or CSV)",
    type=["xlsx", "csv"]
)

if not uploaded_file:
    st.stop()

# ---------------- LOAD DATA ----------------
if uploaded_file.name.endswith(".csv"):
    df = pd.read_csv(uploaded_file)
else:
    df = pd.read_excel(uploaded_file)

# ---------------- CLEAN COLUMN NAMES ----------------
df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

# ---------------- COLUMN ALIAS MAP ----------------
COLUMN_ALIASES = {
    "member_id": ["member_id", "id", "customer_id", "user_id"],
    "status": ["status", "churn", "is_active"],
    "plan_type": ["plan_type", "contract_type", "membership"],
    "amount": ["amount", "revenue", "payment"],
    "visit_date": ["visit_date", "date", "attendance_date"]
}

def normalize_columns(df, alias_map):
    df = df.copy()
    for standard, aliases in alias_map.items():
        for col in df.columns:
            if col in aliases:
                df.rename(columns={col: standard}, inplace=True)
                break
    return df

df = normalize_columns(df, COLUMN_ALIASES)

# ---------------- VALIDATION ----------------
required_columns = ["member_id"]

for col in required_columns:
    if col not in df.columns:
        st.error(f"Missing column: {col}")
        st.stop()

# ---------------- BASIC CLEANING ----------------
df["member_id"] = df["member_id"].astype(str)

if "status" in df.columns:
    df["status"] = df["status"].astype(str).str.lower().map({
        "yes": "Active",
        "1": "Active",
        "true": "Active",
        "active": "Active",
        "no": "Inactive",
        "0": "Inactive",
        "false": "Inactive",
        "churned": "Inactive"
    }).fillna("Inactive")

if "amount" in df.columns:
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# ---------------- KPIs ----------------
total_members = df["member_id"].nunique()
active_members = df[df.get("status", "") == "Active"]["member_id"].nunique()
total_revenue = df.get("amount", pd.Series()).sum()
avg_revenue = round(total_revenue / total_members, 2) if total_members else 0

# ---------------- DASHBOARD ----------------
if page == "📊 Dashboard":
    st.header("📊 Business Dashboard")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Members", total_members)
    k2.metric("Active Members", active_members)
    k3.metric("Total Revenue (₹)", total_revenue)
    k4.metric("Avg Revenue / Member", avg_revenue)

    if "status" in df.columns:
        fig = px.pie(
            df,
            names="status",
            title="Active vs Inactive Members"
        )
        st.plotly_chart(fig, use_container_width=True)

    if "plan_type" in df.columns:
        fig2 = px.bar(
            df["plan_type"].value_counts().reset_index(),
            x="index",
            y="plan_type",
            title="Membership Distribution"
        )
        st.plotly_chart(fig2, use_container_width=True)

# ---------------- ATTENDANCE ----------------
if page == "🏃 Attendance":
    st.header("🏃 Attendance Insights")

    if "visit_date" in df.columns:
        visit_count = df.groupby("member_id").size().reset_index(name="visits")
        st.dataframe(visit_count)
    else:
        st.warning("Attendance data not available")

# ---------------- RISK ANALYSIS ----------------
if page == "⚠️ Risk Analysis":
    st.header("⚠️ Member Risk Analysis")

    visit_count = df.groupby("member_id").size().reset_index(name="visits")

    def risk(v):
        if v <= 2:
            return "High Risk"
        elif v <= 5:
            return "Medium Risk"
        return "Low Risk"

    visit_count["risk_level"] = visit_count["visits"].apply(risk)

    st.dataframe(visit_count)

    fig = px.bar(
        visit_count,
        x="risk_level",
        title="Churn Risk Distribution"
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------- RAW DATA ----------------
if page == "📂 Raw Data":
    st.header("📂 Raw Uploaded Data")
    st.dataframe(df)
