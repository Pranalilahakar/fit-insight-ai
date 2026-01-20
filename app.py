import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import bcrypt

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="FitInsight AI", layout="wide")

# =====================================================
# DATABASE (AUTH ONLY)
# =====================================================
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

# =====================================================
# SESSION STATE
# =====================================================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = None

# =====================================================
# AUTH FUNCTIONS
# =====================================================
def signup(email, password):
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cursor.execute(
            "INSERT INTO users (email, password) VALUES (?, ?)",
            (email, hashed)
        )
        conn.commit()
        return True
    except:
        return False

def login(email, password):
    cursor.execute(
        "SELECT password FROM users WHERE email = ?",
        (email,)
    )
    result = cursor.fetchone()
    if result and bcrypt.checkpw(password.encode(), result[0]):
        return True
    return False

# =====================================================
# LOGIN / SIGNUP PAGE
# =====================================================
if not st.session_state.logged_in:
    st.title("🔐 FitInsight AI – Login")

    choice = st.radio("Login / Signup", ["Login", "Signup"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if choice == "Signup":
        if st.button("Create Account"):
            if signup(email, password):
                st.success("Account created! Please login.")
            else:
                st.error("User already exists.")

    else:
        if st.button("Login"):
            if login(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.experimental_rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("🏋️ FitInsight AI")
st.sidebar.caption("Gym Business Intelligence")
st.sidebar.markdown(f"👤 {st.session_state.user_email}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.experimental_rerun()

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "🏃 Attendance", "⚠️ Risk Analysis", "📂 Raw Data"]
)

# =====================================================
# HEADER
# =====================================================
st.title("🏋️ FitInsight AI – Gym Analytics SaaS")
st.write("Upload your gym Excel file to get instant business insights.")

st.info(
    "🔐 Data Privacy Notice\n\n"
    "• Your data is processed temporarily\n"
    "• Files are NOT stored permanently\n"
    "• No data is shared with third parties"
)

# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_file = st.file_uploader("Upload Gym Excel File", type=["xlsx"])

if not uploaded_file:
    st.warning("⬆️ Please upload an Excel file to continue.")
    st.stop()

# =====================================================
# LOAD DATA
# =====================================================
try:
    members = pd.read_excel(uploaded_file, sheet_name="members")
    attendance = pd.read_excel(uploaded_file, sheet_name="attendance")
    payments = pd.read_excel(uploaded_file, sheet_name="payments")
except Exception:
    st.error(
        "❌ Excel format error\n\n"
        "Required sheets:\n"
        "- members\n- attendance\n- payments\n"
        "All names must be lowercase."
    )
    st.stop()

st.success("✅ File uploaded successfully!")

# =====================================================
# REQUIRED COLUMNS (EXTRA COLUMNS SAFE)
# =====================================================
REQUIRED_MEMBERS = ["member_id", "status", "plan_type", "trainer_name"]
REQUIRED_PAYMENTS = ["member_id", "amount"]

for col in REQUIRED_MEMBERS:
    if col not in members.columns:
        st.error(f"Missing column in members sheet: {col}")
        st.stop()

for col in REQUIRED_PAYMENTS:
    if col not in payments.columns:
        st.error(f"Missing column in payments sheet: {col}")
        st.stop()

# =====================================================
# KPI CALCULATIONS
# =====================================================
total_members = members["member_id"].nunique()
active_members = members[members["status"] == "Active"]["member_id"].nunique()
total_revenue = payments["amount"].sum()
avg_revenue = round(total_revenue / total_members, 2)

# =====================================================
# ATTENDANCE + RISK LOGIC
# =====================================================
attendance_count = (
    attendance.groupby("member_id")
    .size()
    .reset_index(name="visit_count")
)

members_attendance = members.merge(
    attendance_count, on="member_id", how="left"
)

members_attendance["visit_count"] = members_attendance["visit_count"].fillna(0)

def risk_label(v):
    if v <= 2:
        return "High Risk"
    elif v <= 5:
        return "Medium Risk"
    else:
        return "Low Risk"

members_attendance["risk_level"] = members_attendance["visit_count"].apply(risk_label)

# =====================================================
# DASHBOARD PAGE
# =====================================================
if page == "📊 Dashboard":
    st.markdown("## 📊 Business Dashboard")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Members", total_members)
    k2.metric("Active Members", active_members)
    k3.metric("Total Revenue (₹)", total_revenue)
    k4.metric("Avg Revenue / Member", avg_revenue)

    revenue_by_plan = (
        members.merge(payments, on="member_id")
        .groupby("plan_type")["amount"]
        .sum()
        .reset_index()
    )

    fig_bar = px.bar(
        revenue_by_plan,
        x="plan_type",
        y="amount",
        title="Revenue by Plan Type",
        text_auto=True
    )

    status_count = members["status"].value_counts().reset_index()
    status_count.columns = ["status", "count"]

    fig_donut = px.pie(
        status_count,
        names="status",
        values="count",
        hole=0.5,
        title="Member Status Distribution"
    )

    col1, col2 = st.columns(2)
    col1.plotly_chart(fig_bar, use_container_width=True)
    col2.plotly_chart(fig_donut, use_container_width=True)

# =====================================================
# ATTENDANCE PAGE
# =====================================================
elif page == "🏃 Attendance":
    st.markdown("## 🏃 Attendance Insights")
    st.dataframe(
        members_attendance[["member_id", "trainer_name", "visit_count"]]
    )

    csv = members_attendance[
        ["member_id", "trainer_name", "visit_count"]
    ].to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download Attendance Report (CSV)",
        csv,
        "attendance_report.csv",
        "text/csv"
    )

# =====================================================
# RISK PAGE
# =====================================================
elif page == "⚠️ Risk Analysis":
    st.markdown("## ⚠️ High Risk Members")

    high_risk = members_attendance[
        members_attendance["risk_level"] == "High Risk"
    ][["member_id", "visit_count", "risk_level"]]

    st.dataframe(high_risk)

    csv = high_risk.to_csv(index=False).encode("utf-8")

    st.download_button(
        "⬇️ Download High Risk Members (CSV)",
        csv,
        "high_risk_members.csv",
        "text/csv"
    )

# =====================================================
# RAW DATA PAGE
# =====================================================
elif page == "📂 Raw Data":
    tab1, tab2, tab3 = st.tabs(["Members", "Attendance", "Payments"])
    with tab1:
        st.dataframe(members)
    with tab2:
        st.dataframe(attendance)
    with tab3:
        st.dataframe(payments)

