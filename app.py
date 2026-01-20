import streamlit as st
import pandas as pd

st.set_page_config(page_title="FitInsight AI", layout="wide")

st.title("🏋️ FitInsight AI – Gym Analytics SaaS")
st.write("Upload your gym Excel file to get instant insights.")

uploaded_file = st.file_uploader(
    "Upload Gym Excel File",
    type=["xlsx"]
)

if uploaded_file:
    try:
        members = pd.read_excel(uploaded_file, sheet_name="members")
        attendance = pd.read_excel(uploaded_file, sheet_name="attendance")
        payments = pd.read_excel(uploaded_file, sheet_name="payments")

        st.success("✅ File uploaded successfully!")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Members Data")
            st.dataframe(members)

        with col2:
            st.subheader("Payments Data")
            st.dataframe(payments)

    except Exception as e:
        st.error("❌ Error reading file. Please check sheet names.")
        st.exception(e)
