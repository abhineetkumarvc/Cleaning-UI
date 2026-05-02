import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

# --- Page Config ---
st.set_page_config(
    page_title="Flipkart Payment Cleaning Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Background ---
page_bg_css = """
<style>
[data-testid="stAppViewContainer"] {
    background: linear-gradient(to right, #008000, #0000FF);
}
[data-testid="stHeader"] {
    background: none;
}
[data-testid="stSidebar"] {
    background-color: #0000FF;
}
h1 {
    color: white;
    text-align: center;
}
</style>
"""
st.markdown(page_bg_css, unsafe_allow_html=True)

# --- Custom Header ---
st.markdown("<h1>Flipkart Payment Billing Tool</h1>", unsafe_allow_html=True)

# --- Login System ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

def login():
    password = st.text_input("Enter Password", type="password", key="login_password")
    if st.button("Login", key="login_button"):
        if password == "flipkart@2026":  # <-- Replace with your secure password
            st.session_state.authenticated = True
            st.success("✅ Logged in successfully!")
        else:
            st.error("❌ Incorrect password")

def logout():
    if st.button("Logout", key="logout_button"):
        st.session_state.authenticated = False
        st.info("🔒 Logged out")

# --- Authentication Check ---
if not st.session_state.authenticated:
    login()
else:
    logout()
    st.write("Welcome to Flipkart Payment Cleaning Tool!")

    # --- Tabs Setup ---
    tabs = st.tabs([
        "EBRC 1–13 RC",
        "EBRC Fully Live",
        "North EBRC",
        "Consolidated",
        "Shopsy & Non Shopsy",
        "North EBRC Merged",
        "Manual File Split",
        "Support"
    ])

    # -------------------------------
    # TAB 1: EBRC 1–13 RC
    # -------------------------------
    with tabs[0]:
        st.subheader("📊 EBRC 1–13 RC Data Cleaning")
        uploaded_file = st.file_uploader(
            "📂 Upload Invoice Report CSV (EBRC 1–13 RC)",
            type=["csv"],
            key="ebrc_1to13_uploader"
        )

        if uploaded_file and st.button("▶ Process EBRC 1–13 RC", key="process_ebrc_1to13"):
            wanted_cols = [
                "Casper Profile ID","Vendor id","WM Name","Hub Name","From Date","To Date","Vendor name",
                "Payments Calculated","Rate Card Used","Metadata","Cluster Id","Cluster Name",
                "Manual Payout Description","Cost Type","Remarks",
                "number_of_shipments_ratecard_output","u2s_aggregate_exclusion_ratecard_output",
                "number_of_delivered_shipments_ratecard_output","number_of_document_shipments_delivered_ratecard_output"
            ]
            try:
                data = pd.read_csv(uploaded_file, usecols=wanted_cols, engine="python")
            except Exception as e:
                st.error(f"⚠️ Error reading file: {e}")
                st.stop()

            # Rename outputs to inputs
            data = data.rename(columns={
                'number_of_shipments_ratecard_output': 'number_of_shipments_ratecard_input',
                'u2s_aggregate_exclusion_ratecard_output': 'u2s_aggregate_exclusion_ratecard_input',
                'number_of_delivered_shipments_ratecard_output': 'number_of_delivered_shipments_ratecard_input',
                'number_of_document_shipments_delivered_ratecard_output': 'number_of_document_delivered_shipments_ratecard_input'
            })

            # Date conversions
            data['From Date'] = pd.to_datetime(data['From Date'], errors='coerce')
            data['To Date'] = pd.to_datetime(data['To Date'], errors='coerce')

            # Excel-style serial conversion
            excel_base_date = datetime.datetime(1899, 12, 30)
            data['From Date Serial'] = (data['From Date'] - excel_base_date).dt.days

            # Combined identifier
            data['Casper Profile ID/From Date'] = (
                data['Casper Profile ID'].astype(str) + '/' + data['From Date Serial'].astype(str)
            )

            # Filter EBRC 1–13
            filtered_data = data[data['Rate Card Used'].str.match(r'^EBRC_(?:[1-9]|1[0-3])_', na=False)]
            filtered_data = filtered_data.drop(columns=['From Date Serial'])

            desired_cols = wanted_cols[:-4] + [
                "number_of_shipments_ratecard_input","u2s_aggregate_exclusion_ratecard_input",
                "number_of_delivered_shipments_ratecard_input","number_of_document_delivered_shipments_ratecard_input",
                "Casper Profile ID/From Date"
            ]

            if not filtered_data.empty:
                cleaned_data = filtered_data[desired_cols]
                st.success("✅ EBRC 1–13 RC Data cleaned successfully!")
                st.dataframe(cleaned_data, use_container_width=True)

                output = BytesIO()
                cleaned_data.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download EBRC 1–13 Cleaned Data (XLSX)",
                    data=output.getvalue(),
                    file_name="EBRC_1to13_Cleaned_Data.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_ebrc_1to13"
                )
            else:
                st.warning("⚠️ No EBRC 1–13 RC data found in this file.")

    # -------------------------------
    # TAB 2: EBRC Fully Live
    # -------------------------------
    with tabs[1]:
        st.subheader("📊 EBRC Fully Live Data Cleaning")
        uploaded_file_live = st.file_uploader(
            "📂 Upload Invoice Report CSV (EBRC Fully Live)",
            type=["csv"],
            key="ebrc_fully_live_uploader"
        )

        if uploaded_file_live and st.button("▶ Process EBRC Fully Live", key="process_ebrc_fully_live"):
            try:
                df = pd.read_csv(uploaded_file_live, engine="python")
            except Exception as e:
                st.error(f"⚠️ Error reading file: {e}")
                st.stop()

            # Extract rate card number
            df['RateCardNum'] = df['Rate Card Used'].str.extract(r'^EBRC_(\d+)_').astype(float)

            # Filter EBRC >= 14 and exclude unwanted clusters
            filtered_data = df[(df['RateCardNum'] >= 14)]
            filtered_data = filtered_data[~filtered_data['Cluster Name'].isin(['Self van', 'BYOV'])]

            if not filtered_data.empty:
                st.success("✅ EBRC Fully Live Data cleaned successfully!")
                st.dataframe(filtered_data, use_container_width=True)

                output = BytesIO()
                filtered_data.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download EBRC Fully Live Data (XLSX)",
                    data=output.getvalue(),
                    file_name="EBRC_Fully_Live.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_ebrc_fully_live"
                )
            else:
                st.warning("⚠️ No EBRC Fully Live data found in this file.")

    # -------------------------------
    # TAB 3: North EBRC
    # -------------------------------
    with tabs[2]:
        st.header("📊 North EBRC Data Cleaning")
        uploaded_file_north = st.file_uploader(
            "📂 Upload Invoice Report CSV (North EBRC)",
            type=["csv"],
            key="north_ebrc_uploader"
        )

        if uploaded_file_north and st.button("▶ Process North EBRC", key="process_north_ebrc"):
            wanted_cols = [
                "Casper Profile ID","Vendor id","WM Name","Hub Name","From Date","To Date","Vendor name",
                "Payments Calculated","Rate Card Used","Metadata","Cluster Id","Cluster Name",
                "Manual Payout Description","Cost Type","Remarks",
                "U2S_live_status_ratecard_output","seller_delivery_live_status_ratecard_output",
                "Shopsy_live_status_ratecard_output","number_of_shipments_ratecard_output",
                "number_of_delivered_shipments_ratecard_output","u2s_aggregate_exclusion_ratecard_output",
                "number_of_document_delivered_shipments_ratecard_output",
                "number_of_Shopsy_Forward_shipments_ratecard_output",
                "number_of_Shopsy_Forward_delivered_shipments_ratecard_output",
                "number_of_shipments_seller_delivery_delivered_ratecard_output",
                "number_of_pp_shipments_delivered_ratecard_output",
                "number_of_grocery_shipments_assigned_ratecard_output",
                "number_of_grocery_shipments_delivered_ratecard_output",
                "number_of_kyc_shipments_assigned_ratecard_output",
                "number_of_kyc_shipments_delivered_ratecard_output",
                "number_of_LD_assigned_shipments_ratecard_output",
                "number_of_LD_delivered_shipments_ratecard_output",
                "number_of_HD_assigned_shipments_ratecard_output",
                "number_of_HD_delivered_shipments_ratecard_output",
                "number_of_UT_assigned_shipments_ratecard_output",
                "number_of_UT_delivered_shipments_ratecard_output",
                "number_of_NA_assigned_shipments_ratecard_output",
                "number_of_NA_delivered_shipments_ratecard_output",
                "number_of_UHD_assigned_shipments_ratecard_output",
                "number_of_UHD_delivered_shipments_ratecard_output",
                "number_of_shipments_seller_delivery_assigned_ratecard_output",
                "number_of_MD_assigned_shipments_ratecard_output",
                "number_of_MD_delivered_shipments_ratecard_output",
                "number_of_DEFAULT_assigned_shipments_ratecard_output",
                "number_of_DEFAULT_delivered_shipments_ratecard_output"
            ]

            try:
                data_north = pd.read_csv(uploaded_file_north, usecols=wanted_cols, engine="python")
            except Exception as e:
                st.error(f"⚠️ Error reading file: {e}")
                st.stop()

            # Date conversions
            data_north['From Date'] = pd.to_datetime(data_north['From Date'], errors='coerce')
            data_north['To Date'] = pd.to_datetime(data_north['To Date'], errors='coerce')

            # Excel-style serial conversion
            excel_base_date = datetime.datetime(1899, 12, 30)
            data_north['From Date Serial'] = (data_north['From Date'] - excel_base_date).dt.days

            # Combined identifier
            data_north['Casper Profile ID/From Date'] = (
                data_north['Casper Profile ID'].astype(str) + '/' + data_north['From Date Serial'].astype(str)
            )

            # Filter only NORTH_EBRC rows
            filtered_data_north = data_north[data_north['Rate Card Used'].str.startswith('NORTH_EBRC', na=False)]
            filtered_data_north = filtered_data_north.drop(columns=['From Date Serial'])

            desired_cols = wanted_cols + ["Casper Profile ID/From Date"]

            if not filtered_data_north.empty:
                cleaned_data = filtered_data_north[desired_cols]
                st.success("✅ NORTH_EBRC Data cleaned and reordered successfully!")
                st.dataframe(cleaned_data, use_container_width=True)

                output = BytesIO()
                cleaned_data.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download NORTH_EBRC Cleaned Data (XLSX)",
                    data=output.getvalue(),
                    file_name="TF_EBRC_North_EBRC_MIS.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_north_ebrc"
                )
            else:
                st.warning("⚠️ No NORTH_EBRC data found in this file.")

    # -------------------------------
    # TAB 4: Consolidated
    # -------------------------------
    with tabs[3]:
        st.header("📊 Consolidated Kirana Accruals")
        uploaded_files = st.file_uploader(
            "📂 Upload multiple CSV/XLSX files for consolidation",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            key="consolidated_uploader"
        )

        if uploaded_files and st.button("▶ Run Consolidation", key="run_consolidation"):
            dataframes = []
            error_log = []
            for uploaded_file in uploaded_files:
                try:
                    if uploaded_file.name.lower().endswith(".csv"):
                        df = pd.read_csv(uploaded_file, engine="python")
                    else:
                        df = pd.read_excel(uploaded_file)
                    df["SourceFile"] = uploaded_file.name
                    dataframes.append(df)
                except Exception as e:
                    error_log.append((uploaded_file.name, str(e)))
                    st.warning(f"⚠️ Skipping {uploaded_file.name}: {e}")

            if dataframes:
                consolidated_df = pd.concat(dataframes, ignore_index=True, sort=False)
                consolidated_df.fillna(0, inplace=True)

                st.success("✅ Consolidation complete!")
                st.dataframe(consolidated_df, use_container_width=True)

                output = BytesIO()
                consolidated_df.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download Consolidated Data (XLSX)",
                    data=output.getvalue(),
                    file_name="KIRANA_ACCRUALS_CONSOLIDATED.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_consolidated"
                )

                if error_log:
                    log_df = pd.DataFrame(error_log, columns=["File", "Error"])
                    log_buf = BytesIO()
                    log_df.to_csv(log_buf, index=False)
                    st.download_button(
                        label="⬇️ Download Error Log (CSV)",
                        data=log_buf.getvalue(),
                        file_name="consolidation_error_log.csv",
                        mime="text/csv",
                        key="download_consolidation_errors"
                    )
            else:
                st.warning("⚠️ No valid CSV or Excel files found for consolidation.")

    # -------------------------------
    # TAB 5: Shopsy & Non Shopsy Merged
    # -------------------------------
    with tabs[4]:
        st.header("📊 Shopsy & Non Shopsy Merged")

        uploaded_files_shopsy = st.file_uploader(
            "📂 Upload multiple CSV/XLSX files for Shopsy & Non Shopsy consolidation",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            key="shopsy_uploader"
        )

        if uploaded_files_shopsy and st.button("▶ Run Shopsy Consolidation", key="run_shopsy_consolidation"):
            selected_columns = [
                'Casper Profile ID', 'Vendor id', 'WM Name', 'Hub Name', 'From Date', 'To Date',
                'Vendor name', 'Payments Calculated', 'Rate Card Used', 'Metadata', 'Cluster Id',
                'Cluster Name', 'Manual Payout Description', 'Cost Type', 'Remarks',
                'number_of_shipments_ratecard_input', 'u2s_aggregate_exclusion_ratecard_input',
                'number_of_delivered_shipments_ratecard_input', 'Casper Profile ID/From Date',
                'number_of_Shopsy_Forward_shipments_ratecard_input',
                'number_of_Shopsy_Forward_delivered_shipments_ratecard_input', 'key',
                'Rate Card', 'U2S', 'State', 'Zone', 'TnC Zone', 'TnC Tier', 'Final Payout',
                'Rate Card Status', 'old construct earning at 90%', 'Non shopsy Shipment',
                'Differential Payout'
            ]

            dataframes = []
            error_log = []
            for uploaded_file in uploaded_files_shopsy:
                try:
                    if uploaded_file.name.lower().endswith(".csv"):
                        df = pd.read_csv(uploaded_file, engine="python")
                    else:
                        df = pd.read_excel(uploaded_file)

                    missing_cols = [col for col in selected_columns if col not in df.columns]
                    if missing_cols:
                        error_log.append((uploaded_file.name, f"Missing columns: {missing_cols}"))
                        st.warning(f"⚠️ Skipping {uploaded_file.name}: Missing columns {missing_cols}")
                        continue

                    df = df[selected_columns]
                    df["SourceFile"] = uploaded_file.name

                    # Convert 'From Date' to datetime
                    df['From Date'] = pd.to_datetime(df['From Date'], errors='coerce')

                    # Excel-style serial conversion
                    excel_base_date = datetime.datetime(1899, 12, 30)
                    df['From Date Serial'] = (df['From Date'] - excel_base_date).dt.days

                    # Combine fields into a new identifier
                    df['Vendor id/Hub Name/From Date'] = (
                        df['Casper Profile ID'].astype(str) + '/' +
                        df['Hub Name'].astype(str) + '/' +
                        df['From Date Serial'].astype(str)
                    )

                    dataframes.append(df)
                except Exception as e:
                    error_log.append((uploaded_file.name, str(e)))
                    st.warning(f"⚠️ Skipping {uploaded_file.name}: {e}")

            if dataframes:
                consolidated_df = pd.concat(dataframes, ignore_index=True)
                st.success("✅ Shopsy & Non Shopsy Consolidation complete!")
                st.dataframe(consolidated_df, use_container_width=True)

                output = BytesIO()
                consolidated_df.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download Shopsy & Non Shopsy Consolidated Data (XLSX)",
                    data=output.getvalue(),
                    file_name="Shopsy_NonShopsy_Consolidated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_shopsy_consolidated"
                )

                if error_log:
                    log_df = pd.DataFrame(error_log, columns=["File", "Error"])
                    log_buf = BytesIO()
                    log_df.to_csv(log_buf, index=False)
                    st.download_button(
                        label="⬇️ Download Shopsy Error Log (CSV)",
                        data=log_buf.getvalue(),
                        file_name="shopsy_error_log.csv",
                        mime="text/csv",
                        key="download_shopsy_errors"
                    )
            else:
                st.warning("⚠️ No valid CSV or Excel files found or all files were skipped due to errors.")

    # -------------------------------
    # TAB 6: North EBRC Merged
    # -------------------------------
    with tabs[5]:
        st.header("📊 North EBRC Consolidated")

        uploaded_files_north_merge = st.file_uploader(
            "📂 Upload multiple CSV/XLSX files for North EBRC consolidation",
            type=["csv", "xlsx"],
            accept_multiple_files=True,
            key="north_ebrc_merge_uploader"
        )

        if uploaded_files_north_merge and st.button("▶ Run North EBRC Consolidation", key="run_north_ebrc_merge"):
            selected_columns = [
                'Casper Profile ID', 'Vendor id', 'WM Name', 'Hub Name', 'From Date', 'To Date',
                'Vendor name', 'Payments Calculated', 'Rate Card Used', 'Metadata', 'Cluster Id',
                'Cluster Name', 'Manual Payout Description', 'Cost Type', 'Remarks',
                'number_of_shipments_ratecard_output', 'u2s_aggregate_exclusion_ratecard_output',
                'number_of_delivered_shipments_ratecard_output', 'Casper Profile ID/From Date',
                'number_of_Shopsy_Forward_shipments_ratecard_output',
                'number_of_Shopsy_Forward_delivered_shipments_ratecard_output', 'key',
                'Rate Card', 'U2S', 'State', 'Zone', 'TnC Zone', 'TnC Tier', 'Final Payout',
                'Rate Card Status', 'old construct earning at 90%', 'Non shopsy Shipment',
                'Differential Payout'
            ]

            dataframes = []
            error_log = []
            for uploaded_file in uploaded_files_north_merge:
                try:
                    if uploaded_file.name.lower().endswith(".csv"):
                        df = pd.read_csv(uploaded_file, engine="python")
                    else:
                        df = pd.read_excel(uploaded_file)

                    missing_cols = [col for col in selected_columns if col not in df.columns]
                    if missing_cols:
                        error_log.append((uploaded_file.name, f"Missing columns: {missing_cols}"))
                        st.warning(f"⚠️ Skipping {uploaded_file.name}: Missing columns {missing_cols}")
                        continue

                    df = df[selected_columns]
                    df["SourceFile"] = uploaded_file.name

                    # Convert 'From Date' to datetime
                    df['From Date'] = pd.to_datetime(df['From Date'], errors='coerce')

                    # Excel-style serial conversion
                    excel_base_date = datetime.datetime(1899, 12, 30)
                    df['From Date Serial'] = (df['From Date'] - excel_base_date).dt.days

                    # Combine fields into a new identifier
                    df['Vendor id/Hub Name/From Date'] = (
                        df['Casper Profile ID'].astype(str) + '/' +
                        df['Hub Name'].astype(str) + '/' +
                        df['From Date Serial'].astype(str)
                    )

                    dataframes.append(df)
                except Exception as e:
                    error_log.append((uploaded_file.name, str(e)))
                    st.warning(f"⚠️ Skipping {uploaded_file.name}: {e}")

            if dataframes:
                consolidated_df = pd.concat(dataframes, ignore_index=True)
                st.success("✅ North EBRC Consolidation complete!")
                st.dataframe(consolidated_df, use_container_width=True)

                output = BytesIO()
                consolidated_df.to_excel(output, index=False)
                st.download_button(
                    label="⬇️ Download North EBRC Consolidated Data (XLSX)",
                    data=output.getvalue(),
                    file_name="North_EBRC_Consolidated.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="download_north_ebrc_consolidated"
                )

                if error_log:
                    log_df = pd.DataFrame(error_log, columns=["File", "Error"])
                    log_buf = BytesIO()
                    log_df.to_csv(log_buf, index=False)
                    st.download_button(
                        label="⬇️ Download North EBRC Error Log (CSV)",
                        data=log_buf.getvalue(),
                        file_name="north_ebrc_error_log.csv",
                        mime="text/csv",
                        key="download_north_ebrc_errors"
                    )
            else:
                st.warning("⚠️ No valid CSV or Excel files were found or all files were skipped due to errors.")

    # -------------------------------
    # TAB 7: Manual Upload Split
    # -------------------------------
    with tabs[6]:
        st.header("📊 Manual Upload Split")

        uploaded_file_manual = st.file_uploader(
            "📂 Upload Excel file for manual split",
            type=["xlsx"],
            key="manual_split_uploader"
        )

        # User input for chunk size
        chunk_size = st.number_input(
            "Enter chunk size (rows per file)",
            min_value=100,
            max_value=10000,
            value=1000,
            step=100,
            key="manual_chunk_size"
        )

        # User input for group names
        group_names_input = st.text_area(
            "Enter group names (comma-separated)",
            value="Abhi,Sandeep,Teja,Shweta,Ganesh",
            key="manual_group_names"
        )
        group_names = [name.strip() for name in group_names_input.split(",") if name.strip()]

        # User input for how many files each group should handle
        files_per_group = st.number_input(
            "Enter number of files per group before switching",
            min_value=1,
            max_value=50,
            value=22,
            key="manual_files_per_group"
        )

        # User input for base output name
        base_name = st.text_input(
            "Enter base output name (e.g., 'NorthEBRC')",
            value="output",
            key="manual_base_name"
        )

        if uploaded_file_manual and st.button("▶ Run Manual Split", key="run_manual_split"):
            try:
                df = pd.read_excel(uploaded_file_manual, engine="openpyxl")

                output_files = []
                for i in range(0, len(df), chunk_size):
                    chunk = df.iloc[i:i+chunk_size]
                    file_number = i // chunk_size + 1

                    # Determine group name based on file_number and files_per_group
                    group_index = (file_number - 1) // files_per_group
                    if group_index < len(group_names):
                        group_name = group_names[group_index]
                    else:
                        group_name = "Extra"  # fallback label if more groups needed

                    # File name pattern: GroupName_BaseName_outputX.xlsx
                    file_name = f"{group_name}_{base_name}_output{file_number}.xlsx"

                    # Save chunk to BytesIO
                    output = BytesIO()
                    chunk.to_excel(output, index=False, na_rep="")
                    output_files.append((file_name, output.getvalue()))

                st.success("✅ Manual split complete!")
                for file_name, file_data in output_files:
                    st.download_button(
                        label=f"⬇️ Download {file_name}",
                        data=file_data,
                        file_name=file_name,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"download_manual_{file_name}"
                    )

            except Exception as e:
                st.error(f"⚠️ Error processing file: {e}")

    # -------------------------------
    # TAB 8: Support
    # -------------------------------
    with tabs[7]:
        st.header("🛠️ Support & Issue Reporting")

        st.write(
            "If you face any issues or need changes, please raise them here. "
            "Your report will be sent to the support team."
        )

        # Show support email
        st.info("📧 All issues will be sent to: abhineetkumar.vc@flipkart.com")

        # Input fields for support request
        user_name = st.text_input("Your Name", key="support_name")
        user_email = st.text_input("Your Email", key="support_email")
        issue_type = st.selectbox(
            "Issue Type",
            ["Bug", "Feature Request", "Data Issue", "Other"],
            key="support_issue_type"
        )
        issue_description = st.text_area("Describe the issue or request", key="support_description")

        if st.button("▶ Submit Issue", key="submit_support_issue"):
            if user_name and user_email and issue_description:
                # Confirmation message
                st.success(
                    f"✅ Thank you {user_name}, your issue has been recorded. "
                    f"Our support team will reach out to you at {user_email}."
                )

                # Display summary
                st.write("**📋 Issue Summary:**")
                st.write(f"- Type: {issue_type}")
                st.write(f"- Description: {issue_description}")
                st.write(f"- Reporter: {user_name} ({user_email})")
                st.write(f"- Sent to: abhineetkumar.vc@flipkart.com")

                # Optional: create an in-memory record (not persisted)
                # You can extend this to send an email or save to a DB
                issue_record = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "reporter": user_name,
                    "email": user_email,
                    "type": issue_type,
                    "description": issue_description
                }
                st.json(issue_record)
            else:
                st.warning("⚠️ Please fill in all required fields before submitting.")
