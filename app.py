import streamlit as st
import pandas as pd
import plotly.express as px

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(
    page_title="FitInsight AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# GLOBAL STYLES (DARK POWER BI LOOK)
# =====================================================
st.markdown("""
<style>
body { background-color:#0b1220; }
.block-container { padding-top:1.5rem; }

.kpi-card {
    background: linear-gradient(135deg, #1e293b, #020617);
    padding: 22px;
    border-radius: 18px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.45);
    text-align: center;
}
.kpi-title { font-size:14px; color:#94a3b8; }
.kpi-value { font-size:34px; font-weight:bold; color:#38bdf8; }

.section {
    background:#020617;
    padding:24px;
    border-radius:18px;
    margin-top:25px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPER FUNCTIONS
# =====================================================
def clean_columns(df):
    df.columns = (
        df.columns.astype(str)
        .str.lower()
        .str.strip()
        .str.replace(" ", "_")
        .str.replace("-", "_")
    )
    return df

def kpi(title, value):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
    </div>
    """, unsafe_allow_html=True)

# =====================================================
# SIDEBAR NAVIGATION (BUTTONS)
# =====================================================
st.sidebar.markdown("## 🏋️ FitInsight AI")
st.sidebar.caption("Smart Gym Analytics & Automation")

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

if st.sidebar.button("📊 Dashboard"):
    st.session_state.page = "dashboard"
if st.sidebar.button("🏃 Attendance"):
    st.session_state.page = "attendance"
if st.sidebar.button("⚠️ Risk & Churn"):
    st.session_state.page = "risk"
if st.sidebar.button("📁 Data Explorer"):
    st.session_state.page = "data"

page = st.session_state.page

# =====================================================
# HEADER
# =====================================================
st.markdown("## 📈 FitInsight AI – Gym Business Intelligence")
st.info("🔒 Data Privacy: Data is processed in memory only. No files are stored.")

# =====================================================
# FILE UPLOAD
# =====================================================
uploaded_file = st.file_uploader(
    "Upload Gym Data (CSV or Excel)",
    type=["csv", "xlsx"]
)

if not uploaded_file:
    st.warning("Please upload a CSV or Excel file to continue.")
    st.stop()

# =====================================================
# LOAD DATA
# =====================================================
try:
    if uploaded_file.name.endswith(".csv"):
        members = pd.read_csv(uploaded_file)
        attendance = pd.DataFrame()
        payments = pd.DataFrame()
    else:
        members = pd.read_excel(uploaded_file, sheet_name=0)
        try:
            attendance = pd.read_excel(uploaded_file, sheet_name="attendance")
        except:
            attendance = pd.DataFrame()
        try:
            payments = pd.read_excel(uploaded_file, sheet_name="payments")
        except:
            payments = pd.DataFrame()

    members = clean_columns(members)
    attendance = clean_columns(attendance)
    payments = clean_columns(payments)

except Exception as e:
    st.error("❌ Error reading file")
    st.exception(e)
    st.stop()

# =====================================================
# HANDLE MEMBER ID ISSUES
# =====================================================
if "member_id" not in members.columns:
    alt_ids = [c for c in members.columns if "id" in c]
    if alt_ids:
        members["member_id"] = members[alt_ids[0]]
    else:
        st.error("❌ No member_id column found")
        st.write("Available columns:", members.columns.tolist())
        st.stop()

# =====================================================
# METRICS
# =====================================================
total_members = members["member_id"].nunique()

if "status" in members.columns:
    members["status"] = members["status"].astype(str).str.title()
    active_members = members[members["status"] == "Active"]["member_id"].nunique()
else:
    active_members = 0

inactive_members = total_members - active_members

if not payments.empty and "amount" in payments.columns:
    total_revenue = payments["amount"].sum()
else:
    total_revenue = 0

avg_revenue = round(total_revenue / total_members, 2) if total_members else 0

# =====================================================
# DASHBOARD
# =====================================================
if page == "dashboard":

    st.markdown("### 📊 Business Dashboard")

    c1, c2, c3, c4 = st.columns(4)
    with c1: kpi("Total Members", total_members)
    with c2: kpi("Active Members", active_members)
    with c3: kpi("Inactive Members", inactive_members)
    with c4: kpi("Total Revenue (₹)", total_revenue)

    st.markdown("<div class='section'>", unsafe_allow_html=True)

    if "status" in members.columns:
        status_counts = members["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]

        fig = px.pie(
            status_counts,
            names="status",
            values="count",
            hole=0.6,
            color_discrete_sequence=["#38bdf8", "#f43f5e"]
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )

        st.plotly_chart(fig, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

# =====================================================
# ATTENDANCE
# =====================================================
elif page == "attendance":

    st.markdown("### 🏃 Attendance Insights")

    if attendance.empty or "member_id" not in attendance.columns:
        st.warning("Attendance data not available")
    else:
        visits = attendance.groupby("member_id").size().reset_index(name="visits")

        fig = px.bar(
            visits,
            x="member_id",
            y="visits",
            color="visits",
            color_continuous_scale="Blues"
        )

        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )

        st.plotly_chart(fig, use_container_width=True)

# =====================================================
# RISK & CHURN
# =====================================================
elif page == "risk":

    st.markdown("### ⚠️ Risk & Churn Analysis")

    if attendance.empty:
        st.warning("Attendance data required")
    else:
        visits = attendance.groupby("member_id").size().reset_index(name="visits")

        def risk(v):
            if v <= 2:
                return "High Risk"
            elif v <= 5:
                return "Medium Risk"
            else:
                return "Low Risk"

        visits["risk_level"] = visits["visits"].apply(risk)
        st.dataframe(visits)

# =====================================================
# DATA EXPLORER
# =====================================================
elif page == "data":

    st.markdown("### 📁 Data Explorer")

    t1, t2, t3 = st.tabs(["Members", "Attendance", "Payments"])

    with t1:
        st.dataframe(members)
    with t2:
        st.dataframe(attendance if not attendance.empty else pd.DataFrame())
    with t3:
        st.dataframe(payments if not payments.empty else pd.DataFrame())
