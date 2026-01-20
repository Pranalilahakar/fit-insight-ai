import streamlit as st
import pandas as pd

# ---------------- Page Config ----------------
st.set_page_config(page_title="FitInsight AI", layout="wide")

# ---------------- Sidebar ----------------
st.sidebar.title("FitInsight AI")
page = st.sidebar.radio(
    "Navigate",
    ["Dashboard", "Attendance", "Risk Analysis", "Raw Data"]
)

# ---------------- Header ----------------
st.title("🏋️ FitInsight AI – Gym Analytics SaaS")
st.write("Upload your gym Excel file to get instant insights.")

# ---------------- File Upload ----------------
uploaded_file = st.file_uploader(
    "Upload Gym Excel File",
    type=["xlsx"]
)

if uploaded_file:
    try:
        # -------- Load Data --------
        members = pd.read_excel(uploaded_file, sheet_name="members")
        attendance = pd.read_excel(uploaded_file, sheet_name="attendance")
        payments = pd.read_excel(uploaded_file, sheet_name="payments")

        st.success("✅ File uploaded successfully!")

        # -------- KPI Calculations --------
        total_members = members['member_id'].nunique()
        active_members = members[members['status'] == 'Active']['member_id'].nunique()
        total_revenue = payments['amount'].sum()
        avg_revenue = round(total_revenue / total_members, 2)

        # -------- Attendance Processing --------
        attendance_count = (
            attendance.groupby('member_id')
            .size()
            .reset_index(name='visit_count')
        )

        members_attendance = members.merge(
            attendance_count, on='member_id', how='left'
        )

        members_attendance['visit_count'] = members_attendance['visit_count'].fillna(0)

        # -------- Risk Logic --------
        def risk_label(visits):
            if visits <= 2:
                return "High Risk"
            elif visits <= 5:
                return "Medium Risk"
            else:
                return "Low Risk"

        members_attendance['risk_level'] = members_attendance['visit_count'].apply(risk_label)

        # ================= PAGE RENDERING =================

        if page == "Dashboard":
            st.markdown("## 📊 Business Dashboard")

            k1, k2, k3, k4 = st.columns(4)
            k1.metric("Total Members", total_members)
            k2.metric("Active Members", active_members)
            k3.metric("Total Revenue (₹)", total_revenue)
            k4.metric("Avg Revenue / Member", avg_revenue)

        elif page == "Attendance":
            st.markdown("## 🏃 Attendance Insights")
            st.dataframe(
                members_attendance[['member_id', 'trainer_name', 'visit_count']]
            )

        elif page == "Risk Analysis":
            st.markdown("## ⚠️ High Risk Members")
            st.dataframe(
                members_attendance[members_attendance['risk_level'] == "High Risk"]
            )

        elif page == "Raw Data":
            tab1, tab2, tab3 = st.tabs(["Members", "Attendance", "Payments"])
            with tab1:
                st.dataframe(members)
            with tab2:
                st.dataframe(attendance)
            with tab3:
                st.dataframe(payments)

    except Exception:
        st.error(
            "❌ Excel format error.\n\n"
            "Required sheets:\n"
            "- members\n- attendance\n- payments\n\n"
            "All names must be lowercase."
        )
else:
    st.info("⬆️ Please upload an Excel file to continue.")
