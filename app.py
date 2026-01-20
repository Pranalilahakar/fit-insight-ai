import streamlit as st
import pandas as pd
import sqlite3
import bcrypt
import plotly.express as px

# ---------------- CONFIG ----------------
st.set_page_config(layout="wide", page_title="FitInsight AI")

# ---------------- CUSTOM CSS ----------------
st.markdown("""
<style>
#MainMenu, footer, header {visibility: hidden;}

.stApp {
    background: #F8FAFC;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A, #020617);
    color: white;
}

/* Buttons */
.nav-btn {
    width: 100%;
    padding: 16px;
    margin: 8px 0;
    font-size: 16px;
    border-radius: 14px;
    border: none;
    background: linear-gradient(135deg, #7C3AED, #22C55E);
    color: white;
    cursor: pointer;
}

/* KPI Card */
.card {
    background: white;
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0px 6px 20px rgba(0,0,0,0.08);
    text-align: center;
}
.card h2 {
    color: #7C3AED;
}
</style>
""", unsafe_allow_html=True)

# ---------------- DATABASE ----------------
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

# ---------------- AUTH HELPERS ----------------
def hash_pw(pw):
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt())

def verify_pw(pw, hashed):
    return bcrypt.checkpw(pw.encode(), hashed)

# ---------------- SESSION ----------------
if "logged" not in st.session_state:
    st.session_state.logged = False
if "page" not in st.session_state:
    st.session_state.page = "Overview"

# ---------------- LOGIN ----------------
if not st.session_state.logged:
    st.title("🔐 FitInsight AI Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cursor.execute("SELECT password FROM users WHERE email=?", (email,))
        res = cursor.fetchone()
        if res and verify_pw(password, res[0]):
            st.session_state.logged = True
            st.session_state.email = email
            st.experimental_rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

# ---------------- SIDEBAR ----------------
st.sidebar.image("logo.png", width=120)
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
    st.session_state.logged = False
    st.experimental_rerun()

# ---------------- UPLOAD ----------------
st.markdown("🔒 **Data Privacy:** Files processed in memory only.")
file = st.file_uploader("Upload Gym CSV / Excel", ["csv", "xlsx"])

if not file:
    st.stop()

df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)
df.columns = df.columns.str.lower().str.replace(" ", "_")

# Auto member_id detection
for c in df.columns:
    if c.replace("_", "") in ["memberid", "customerid", "userid", "id"]:
        df.rename(columns={c: "member_id"}, inplace=True)

if "status" not in df.columns:
    df["status"] = "Inactive"

df["status"] = df["status"].astype(str).str.lower().map({
    "active": "Active",
    "inactive": "Inactive",
    "yes": "Active",
    "no": "Inactive"
}).fillna("Inactive")

# ---------------- KPIs ----------------
total = df["member_id"].nunique()
active = df[df["status"] == "Active"]["member_id"].nunique()

# ---------------- PAGES ----------------
if st.session_state.page == "Overview":
    st.markdown("## 📊 Business Overview")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"<div class='card'><h4>Total Members</h4><h2>{total}</h2></div>", unsafe_allow_html=True)
    with c2:
        st.markdown(f"<div class='card'><h4>Active Members</h4><h2>{active}</h2></div>", unsafe_allow_html=True)
    with c3:
        st.markdown(f"<div class='card'><h4>Inactive Members</h4><h2>{total-active}</h2></div>", unsafe_allow_html=True)

    fig = px.pie(df, names="status", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "Analytics":
    st.markdown("## 📈 Member Analytics")
    fig = px.bar(df["status"].value_counts().reset_index(), x="index", y="status")
    st.plotly_chart(fig, use_container_width=True)

elif st.session_state.page == "Risk":
    st.markdown("## ⚠️ Risk Analysis")
    df["risk"] = df["status"].apply(lambda x: "High Risk" if x == "Inactive" else "Low Risk")
    st.dataframe(df[["member_id", "status", "risk"]])

elif st.session_state.page == "Data":
    st.markdown("## 📂 Raw Data")
    st.dataframe(df)
