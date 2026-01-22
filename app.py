import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
import bcrypt
import plotly.express as px
import os
from datetime import datetime

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(
    page_title="FitInsight AI",
    layout="wide"
)

# -------------------------------------------------
# GLOBAL CSS (CLEAN & PROFESSIONAL)
# -------------------------------------------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: linear-gradient(180deg, #f8fafc, #eef2ff);
}

.card {
    background: white;
    padding: 20px;
    border-radius: 16px;
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}

.kpi {
    font-size: 32px;
    font-weight: 700;
    color: #4f46e5;
}

.section {
    font-size: 26px;
    font-weight: 700;
    margin-bottom: 5px;
}

.sub {
    color: #6b7280;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------
# DATABASE (LOGIN)
# -------------------------------------------------
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

# -------------------------------------------------
# AUTH HELPERS
# -------------------------------------------------
def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def verify_pw(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed)

# -------------------------------------------------
# SESSION STATE
# -------------------------------------------------
if "logged" not in st.session_state:
    st.session_state.logged = False
if "page" not in st.session_state:
    st.session_state.page = "Dashboard"

# -------------------------------------------------
# LOGIN PAGE
# -------------------------------------------------
if not st.session_state.logged:
    st.title("🔐 FitInsight AI Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    col1, col2 = st.columns(2)

    if col1.button("Login"):
        cursor.execute("SELECT password FROM users WHERE email=?", (email,))
        user = cursor.fetchone()
        if user and verify_pw(password, user[0]):
            st.session_state.logged = True
            st.session_state.email = email
            st.rerun()
        else:
            st.error("Invalid credentials")

    if col2.button("Sign Up"):
        try:
            cursor.execute(
                "INSERT INTO users (email, password) VALUES (?, ?)",
                (email, hash_pw(password))
            )
            conn.commit()
            st.success("Account created. Login now.")
        except:
            st.error("User already exists")

    st.stop()

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.markdown("## 🏋️ FitInsight AI")
st.sidebar.caption("Smart Gym Analytics & Automation")
st.sidebar.markdown(f"👤 {st.session_state.email}")
st.sidebar.markdown("---")

if st.sidebar.button("📊 Dashboard"):
    st.session_state.page = "Dashboard"
if st.sidebar.button("⚠️ Risk & Churn"):
    st.session_state.page = "Risk"
if st.sidebar.button("⚡ Automation"):
    st.session_state.page = "Automation"
if st.sidebar.button("📂 Data Explorer"):
    st.session_state.page = "Data"

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Logout"):
    st.session_state.logged = False
    st.rerun()

# -------------------------------------------------
# DATA UPLOAD
# -------------------------------------------------
st.info("🔐 Data is processed in memory only. No data is stored.")

file = st.file_uploader("Upload Gym CSV or Excel", ["csv", "xlsx"])
if not file:
    st.stop()

# -------------------------------------------------
# LOAD & CLEAN DATA
# -------------------------------------------------
df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
    .str.replace("-", "_")
)

# Auto-detect member_id
for c in df.columns:
    if c.replace("_", "") in ["memberid", "customerid", "userid", "id"]:
        df.rename(columns={c: "member_id"}, inplace=True)

if "member_id" not in df.columns:
    st.error("❌ Member ID column not found")
    st.stop()

# Status normalization
if "status" not in df.columns:
    df["status"] = "inactive"

df["status"] = df["status"].astype(str).str.lower().map({
    "active": "Active",
    "inactive": "Inactive",
    "yes": "Active",
    "no": "Inactive",
    "1": "Active",
    "0": "Inactive"
}).fillna("Inactive")

# Attendance
if "last_attendance" in df.columns:
    df["last_attendance"] = pd.to_datetime(df["last_attendance"], errors="coerce")
    df["days_since_last"] = (datetime.today() - df["last_attendance"]).dt.days
else:
    df["days_since_last"] = 999

# Revenue
if "amount" not in df.columns:
    df["amount"] = 0
df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

# -------------------------------------------------
# KPIs
# -------------------------------------------------
total_members = df["member_id"].nunique()
active_members = df[df["status"] == "Active"]["member_id"].nunique()
inactive_members = total_members - active_members
total_revenue = int(df["amount"].sum())

# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------
if st.session_state.page == "Dashboard":
    st.markdown('<div class="section">📊 Business Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Overall gym performance</div>', unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f"<div class='card'><div>Total Members</div><div class='kpi'>{total_members}</div></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><div>Active Members</div><div class='kpi'>{active_members}</div></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><div>Inactive Members</div><div class='kpi'>{inactive_members}</div></div>", unsafe_allow_html=True)
    with c4:
        st.markdown(f"<div class='card'><div>Total Revenue</div><div class='kpi'>₹{total_revenue}</div></div>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        fig = px.pie(df, names="status", hole=0.4, title="Member Status")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig2 = px.histogram(df, x="days_since_last", title="Days Since Last Visit")
        st.plotly_chart(fig2, use_container_width=True)

# -------------------------------------------------
# RISK
# -------------------------------------------------
elif st.session_state.page == "Risk":
    st.markdown('<div class="section">⚠️ Risk & Churn</div>', unsafe_allow_html=True)

    df["risk"] = np.where(df["days_since_last"] > 7, "High Risk", "Low Risk")
    high_risk = df[df["risk"] == "High Risk"]

    st.write(f"High Risk Members: {len(high_risk)}")
    st.dataframe(high_risk[["member_id", "days_since_last", "risk"]])

# -------------------------------------------------
# AUTOMATION
# -------------------------------------------------
elif st.session_state.page == "Automation":
    st.markdown('<div class="section">⚡ Automation Center</div>', unsafe_allow_html=True)

    df["risk"] = np.where(df["days_since_last"] > 7, "High Risk", "Low Risk")
    inactive = df[df["risk"] == "High Risk"]

    if inactive.empty:
        st.success("🎉 No inactive members")
    else:
        for _, row in inactive.iterrows():
            st.markdown(f"<div class='card'>Member ID: {row['member_id']}<br>Inactive for {row['days_since_last']} days</div>", unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            if col1.button("📲 Send WhatsApp Reminder", key=f"wa{row['member_id']}"):
                st.success("WhatsApp reminder sent (simulated)")
            if col2.button("📧 Send Email", key=f"em{row['member_id']}"):
                st.success("Email sent (simulated)")

# -------------------------------------------------
# DATA
# -------------------------------------------------
elif st.session_state.page == "Data":
    st.markdown('<div class="section">📂 Data Explorer</div>', unsafe_allow_html=True)
    st.dataframe(df)
