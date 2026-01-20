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
    cursor.execute("SELECT password FROM users WHERE email = ?", (email,))
    result = cursor.fetchone()
    return result and bcrypt.checkpw(password.encode(), result[0])

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
                st.success("Account created. Please login.")
            else:
                st.error("User already exists.")

    else:
        if st.button("Login"):
            if login(email, password):
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.rerun()
            else:
                st.error("Invalid credentials")

    st.stop()

# =====================================================
# SIDEBAR
# =====================================================
st.sidebar.title("🏋️ FitInsight AI")
st.sidebar.markdown(f"👤 {st.session_state.user_email}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_email = None
    st.rerun()

page = st.sidebar.radio(
    "Navigate",
    ["📊 Dashboard", "🏃 Attendance", "⚠️ Risk Analysis", "📂 Raw Data"]
)

# =====================================================
# HEADER
# =====================================================
st.title("🏋️ FitInsight AI – Gym Analytics SaaS")

st.info(
    "🔐 Data Privacy Notice\n"
    "• Data is processed temporarily\n"
    "• No files are stored\n"
    "• No third-party sharing"
)

# =====================================================
# FILE UPLOAD (CSV + EXCEL)
# =====================================================
uploaded_file = st.file_uploader(
    "Upload Gym Data (Excel or CSV)",
    type=["xlsx", "csv"]
)

if not uploaded_file:
    st.warning("Upload a file to continue.")
    st.stop()

# =====================================================
# LOAD DATA
# =====================================================
def load_data(file, sheet=None):
    if file.name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file, sheet_name=sheet)

try:
    if uploaded_file.name.endswith(".xlsx"):
        members = load_data(uploaded_file, "members")
        attendance = load_data(uploaded_file, "attendance")
        payments = load_data(uploaded_file, "payments")
    else:
        members = load_data(uploaded_file)
        attendance = pd.DataFrame()
        payments = pd.DataFrame()
except:
    st.error("Invalid file format or missing sheets.")
    st.stop()

st.success("File uploaded successfully!")

# =====================================================
# REQUIRED COLUMNS
# =====================================================
required_members = ["member_id", "status", "plan_type", "trainer_name"]
required_payments = ["member_id", "amount"]

for col in required_members:
    if col not in members.columns:
        st.error(f"Missing column: {col}")
        st.stop()

# =====================================================
# KPI CALCULATIONS
# =====================================================
total_members = members["member_id"].nunique()
active_members = members[members["status"] == "Active"]["member_id"].nunique()

if not payments.empty:
    total_revenue = payments["amount"].sum()
else:
    total_revenue = 0

avg_revenue = round(total_revenue / total_members, 2) if total_members else 0

# =====================================================
# ATTENDANCE + RISK
# =====================================================
if not attendance.empty:
    visit_count = attendance.groupby("member_id").size().reset_index(name="visit_count")
else:
    visit_count = pd.DataFrame(columns=["member_id", "visit_count"])

members_attendance = members.merge(visit_count, on="member_id", how="left")
members_attendance["visit_count"] = members_attendance["visit_count"].fillna(0)

def risk_label(v):
    if v <= 2:
        return "High Risk"
    elif v <= 5:
        return "Medium Risk"
    return "Low Risk"

members_attendance["risk_level"] = members_attendance["visit_count"].apply(risk_label)

# =====================================================
# DASHBOARD
# =====================================================
if page == "📊 Dashboard":
    st.markdown("## 📊 Business Dashboard")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Members", total_members)
    k2.metric("Active Members", active_members)
    k3.metric("Total Revenue (₹)", total_revenue)
    k4.metric("Avg Revenue / Member", avg_revenue)

    st.markdown("---")

    # Revenue by Plan
    if not payments.empty:
        rev_plan = members.merge(payments, on="member_id") \
            .groupby("plan_type")["amount"].sum().reset_index()

        st.plotly_chart(
            px.bar(rev_plan, x="plan_type", y="amount",
                   title="Revenue by Plan Type", text_auto=True),
            use_container_width=True
        )

    # Status Distribution
    status_df = members["status"].value_counts().reset_index()
    status_df.columns = ["status", "count"]

    st.plotly_chart(
        px.pie(status_df, names="status", values="count",
               title="Member Status Distribution", hole=0.5),
        use_container_width=True
    )

    # Members by Trainer
    trainer_df = members.groupby("trainer_name")["member_id"].nunique().reset_index()

    st.plotly_chart(
        px.bar(trainer_df, x="trainer_name", y="member_id",
               title="Members by Trainer", text_auto=True),
        use_container_width=True
    )

    # Risk Distribution
    risk_df = members_attendance["risk_level"].value_counts().reset_index()
    risk_df.columns = ["risk_level", "count"]

    st.plotly_chart(
        px.bar(risk_df, x="risk_level", y="count",
               title="Risk Level Distribution", text_auto=True),
        use_container_width=True
    )

# =====================================================
# ATTENDANCE
# =====================================================
elif page == "🏃 Attendance":
    st.markdown("## 🏃 Attendance Insights")
    st.dataframe(members_attendance[["member_id", "trainer_name", "visit_count"]])

    csv = members_attendance.to_csv(index=False).encode("utf-8")
    st.download_button("Download Attendance CSV", csv, "attendance.csv", "text/csv")

# =====================================================
# RISK ANALYSIS
# =====================================================
elif page == "⚠️ Risk Analysis":
    high_risk = members_attendance[members_attendance["risk_level"] == "High Risk"]
    st.dataframe(high_risk[["member_id", "visit_count", "risk_level"]])

    csv = high_risk.to_csv(index=False).encode("utf-8")
    st.download_button("Download High Risk CSV", csv, "high_risk.csv", "text/csv")

# =====================================================
# RAW DATA
# =====================================================
elif page == "📂 Raw Data":
    st.dataframe(members)
    if not attendance.empty:
        st.dataframe(attendance)
    if not payments.empty:
        st.dataframe(payments)

