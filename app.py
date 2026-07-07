import streamlit as st
import gspread
import pandas as pd
import plotly.express as px
from oauth2client.service_account import ServiceAccountCredentials

# ==========================================
# ⚙️ SYSTEM CONFIGURATION
# ==========================================
GOOGLE_SHEET_NAME = "TO_DO_LIST" 

# Security Credentials
CORRECT_USER = "admin777"
CORRECT_PASS = "777"

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
# 🔌 AUTO-REPAIR GOOGLE CONNECTION ENGINE
# ==========================================
@st.cache_resource(ttl=20)
def get_google_sheet_client():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        if "gcp_service_account" not in st.secrets:
            st.error("❌ Configuration Error: Please ensure secrets are added to your Streamlit dashboard settings.")
            return None
            
        # Import credentials safely
        creds_dict = dict(st.secrets["gcp_service_account"])
        raw_key = creds_dict.get("private_key", "")
        
        # 🔥 ULTRA RESILIENT AUTO-REPAIR ENGINE FOR PADDING & NEWLINES
        # 1. Clean up literal character escapes
        cleaned_key = raw_key.replace("\\n", "\n").replace("\\blank", "").strip()
        
        # 2. Reconstruct headers if stripped or corrupted
        if "-----BEGIN PRIVATE KEY-----" not in cleaned_key:
            cleaned_key = "-----BEGIN PRIVATE KEY-----\n" + cleaned_key
        if "-----END PRIVATE KEY-----" not in cleaned_key:
            cleaned_key = cleaned_key + "\n-----END PRIVATE KEY-----\n"
            
        # 3. Fix internal formatting and line wrapping
        lines = [line.strip() for line in cleaned_key.split("\n") if line.strip()]
        if len(lines) > 2:
            header = lines[0]
            footer = lines[-1]
            body = "".join(lines[1:-1]).replace(" ", "")
            
            # Auto-adjust base64 string padding lengths
            missing_padding = len(body) % 4
            if missing_padding:
                body += '=' * (4 - missing_padding)
                
            # Piece it back together into standard standard format
            cleaned_key = f"{header}\n{body}\n{footer}\n"
            
        creds_dict["private_key"] = cleaned_key
        
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"🔌 Connection Sync Failed: {e}")
        return None

def fetch_tab_data(tab_name):
    client = get_google_sheet_client()
    if client:
        try:
            sheet = client.open(GOOGLE_SHEET_NAME).worksheet(tab_name)
            records = sheet.get_all_records()
            return pd.DataFrame(records), sheet
        except Exception as e:
            st.error(f"⚠️ Tab Reference Error '{tab_name}': {e}")
            return pd.DataFrame(), None
    return pd.DataFrame(), None

# ==========================================
# 🔑 LOGIN ACCESS CONTROL
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
                st.success("Access Granted! Syncing data streams...")
                st.rerun()
            else:
                st.error("Invalid Security Credentials. Access Denied.")
    
    inject_watermark()
    st.stop()

# ==========================================
# 📊 LIVE DATA PLATFORM
# ==========================================
st.title("🚊 Rake Fault Analytics Control Center")

st.sidebar.header("Navigation Control")
selected_tab = st.sidebar.selectbox("Select Target Data View", ["_AT Tab", "_RAIL Tab"])
sheet_tab_map = {"_AT Tab": "_AT", "_RAIL Tab": "_RAIL"}

# Download spreadsheet data
df, active_worksheet = fetch_tab_data(sheet_tab_map[selected_tab])

if not df.empty:
    # Identify case-insensitive column names safely
    df.columns = [str(c).strip() for c in df.columns]
    status_col = None
    for col in df.columns:
        if col.lower() in ['status', 'fault status', 'state', 'condition']:
            status_col = col
            break

    # --- TOP METRIC BARS ---
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

    # --- DATA PANELS ---
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
            st.info("To view metric visualization graphs, ensure your sheet columns include a header named 'Status'.")

    elif view_mode == "Update Operational Status":
        st.markdown("### 📝 Modify Worksheet Records")
        if status_col:
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
                    st.cache_resource.clear() 
                    st.rerun()
                except Exception as ex:
                    st.error(f"Write operation rejected: {ex}")
        else:
            st.warning("Updating features require a defined status column track inside the worksheet.")
else:
    st.info("⏳ Connecting to secure server buckets... Please ensure your Google Drive service account has 'Editor' access permission shared directly to your Google Sheet.")

if st.sidebar.button("Secure System Log Out"):
    st.session_state.authenticated = False
    st.rerun()

inject_watermark()
