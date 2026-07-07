import streamlit as st
import pandas as pd
import plotly.express as px

# ==========================================
# ⚙️ SYSTEM CONFIGURATION
# ==========================================
# Your exact Google Sheet ID from your shared link
SPREADSHEET_ID = "1ZKTLXv2VQEBG7OUeEo2GoF2Pz4IyYOot"

# Hardcoded Authentication
CORRECT_USER = "admin777"
CORRECT_PASS = "777"

# Streamlit page layout rule (Must be first)
st.set_page_config(page_title="Rake Fault Analytics", page_icon="🚊", layout="wide")

# ==========================================
# 🔒 SECURITY WATERMARK
# ==========================================
def inject_watermark():
    st.markdown(
        """
        <style>
        .niladri-watermark {
            position: fixed;
            bottom: 15px;
            right: 15px;
            background-color: #fff1f1;
            padding: 8px 14px;
            border: 2px solid #ff4b4b;
            border-radius: 6px;
            color: #ff4b4b;
            font-family: 'Courier New', Courier, monospace;
            font-weight: bold;
            font-size: 13px;
            z-index: 999999;
            box-shadow: 2px 2px 12px rgba(0,0,0,0.15);
        }
        </style>
        <div class="niladri-watermark">⚙️ System Core: Made by Niladri Das</div>
        """,
        unsafe_allow_html=True
    )

# ==========================================
# 🔌 ZERO-DEPENDENCY CSV STREAM ENGINE
# ==========================================
@st.cache_data(ttl=10)
def fetch_tab_data(tab_name):
    try:
        # Bypasses openpyxl completely by pulling data through Google's native CSV export endpoint
        csv_url = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq?tqx=out:csv&sheet={tab_name}"
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"⚠️ Live Data Link Stream Blocked: {e}")
        return pd.DataFrame()

def get_gspread_worksheet(tab_name):
    # Isolated write-back connection to prevent any invalid keys from breaking the application view
    try:
        import gspread
        from oauth2client.service_account import ServiceAccountCredentials
        if "gcp_service_account" in st.secrets:
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds_dict = dict(st.secrets["gcp_service_account"])
            if "\\n" in creds_dict.get("private_key", ""):
                creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
            creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
            client = gspread.authorize(creds)
            return client.open_by_key(SPREADSHEET_ID).worksheet(tab_name)
    except Exception:
        return None
    return None

# ==========================================
# 🔑 LOGIN SYSTEM
# ==========================================
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 System Login Portal")
    st.subheader("Rake Fault Analytics Dashboard Engine")
    
    with st.form("login_form"):
        username = st.text_input("User ID", placeholder="Enter Admin ID")
        password = st.text_input("Password", type="password", placeholder="Enter Password")
        login_button = st.form_submit_button("Access System")
        
        if login_button:
            if username == CORRECT_USER and password == CORRECT_PASS:
                st.session_state.authenticated = True
                st.success("Access Granted! Fetching tables...")
                st.rerun()
            else:
                st.error("Invalid Security Credentials. Access Denied.")
    
    inject_watermark()
    st.stop()

# ==========================================
# 📊 CONTROL INTERFACE
# ==========================================
st.title("🚊 Rake Fault Analytics Control Center")

st.sidebar.header("Navigation Control")
selected_tab = st.sidebar.selectbox("Select Target Data View", ["_AT Tab", "_RAIL Tab"])
sheet_tab_map = {"_AT Tab": "_AT", "_RAIL Tab": "_RAIL"}

# Stream the data live
df = fetch_tab_data(sheet_tab_map[selected_tab])

if not df.empty:
    # Safely align and look for status metrics
    df.columns = [str(c).strip() for c in df.columns]
    status_col = None
    for col in df.columns:
        if col.lower() in ['status', 'fault status', 'state', 'condition']:
            status_col = col
            break

    # --- TOP ROW METRIC PANELS ---
    st.markdown("### 📈 Real-Time KPIs")
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Logged Events", len(df))
    
    if status_col:
        open_count = len(df[df[status_col].astype(str).str.strip().lower() == 'open'])
        closed_count = len(df[df[status_col].astype(str).str.strip().lower() == 'closed'])
        m2.metric("Active Open Faults", open_count, delta=f"{open_count} Pending", delta_color="inverse")
        m3.metric("Resolved Closed Faults", closed_count, delta=f"{closed_count} Fixed")
    else:
        m2.metric("Active Open Faults", "N/A")
        m3.metric("Resolved Closed Faults", "N/A")

    st.markdown("---")

    # --- APP NAVIGATION PANELS ---
    view_mode = st.radio("Display Mode", ["Data Explorer Table", "Analytical Charts", "Update Operational Status"], horizontal=True)

    if view_mode == "Data Explorer Table":
        st.markdown(f"### 📋 Active Records for `{sheet_tab_map[selected_tab]}`")
        st.dataframe(df, use_container_width=True)

    elif view_mode == "Analytical Charts":
        st.markdown("### 📊 Distribution Trends")
        if status_col:
            fig = px.pie(df, names=status_col, title="Fault Breakdown Ratio (Open vs Closed)", hole=0.4,
                         color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("To view visual pie metrics, ensure your spreadsheet rows have an explicit column named 'Status'.")

    elif view_mode == "Update Operational Status":
        st.markdown("### 📝 Modify Worksheet Records")
        
        # Safe check for write permission hooks
        active_worksheet = get_gspread_worksheet(sheet_tab_map[selected_tab])
        
        if active_worksheet is None:
            st.warning("⚠️ **Live Table View is Active, but Database Save Access is Locked.**")
            st.info("Your data is displaying successfully! If you want to use this specific tab to modify statuses back to the sheet, fix the formatting of the private key inside your Streamlit Advanced Secrets box.")
        elif status_col:
            row_to_update = st.selectbox("Select Row ID / Index to Update", df.index.tolist())
            current_status = df.loc[row_to_update, status_col]
            
            st.write(f"Current operational status of row **{row_to_update}** is: `{current_status}`")
            new_status = st.selectbox("Assign New Status Value", ["Open", "Closed"])
            
            if st.button("Commit Status Overwrite to Google Cloud"):
                try:
                    gspread_row_num = int(row_to_update) + 2 
                    gspread_col_num = df.columns.get_loc(status_col) + 1
                    
                    active_worksheet.update_cell(gspread_row_num, gspread_col_num, new_status)
                    st.success(f"Successfully updated Row {gspread_row_num} to '{new_status}'!")
                    st.cache_data.clear() 
                    st.rerun()
                except Exception as ex:
                    st.error(f"Write operation rejected: {ex}")
        else:
            st.warning("Spreadsheet track requires a defined 'Status' column header to utilize write-back operations.")
else:
    st.info("⏳ Synchronizing to cloud table link channels...")

if st.sidebar.button("Secure System Log Out"):
    st.session_state.authenticated = False
    st.rerun()

inject_watermark()
