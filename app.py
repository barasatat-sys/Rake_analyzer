import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px

# --- CONFIGURATION & GLOBAL WATERMARK ---
st.set_page_config(page_title="Rake Fault Analytics", layout="wide")

# Persistent HTML/CSS Watermark Injection
watermark_layout = """
<style>
    /* Fixed screen watermark */
    .permanent-watermark {
        position: fixed;
        bottom: 15px;
        right: 15px;
        alpha: 0.8;
        z-index: 999999;
        font-family: 'Courier New', monospace;
        font-size: 13px;
        font-weight: 900;
        color: #FF4B4B;
        background-color: rgba(255, 255, 255, 0.9);
        padding: 6px 12px;
        border: 2px solid #FF4B4B;
        border-radius: 4px;
        box-shadow: 2px 2px 10px rgba(0,0,0,0.15);
        pointer-events: none;
        user-select: none;
    }
    /* Sidebar sticky watermark */
    .sidebar-watermark {
        font-family: 'Courier New', monospace;
        font-size: 12px;
        font-weight: bold;
        color: #888888;
        text-align: center;
        margin-top: 50px;
        border-top: 1px dashed #ccc;
        padding-top: 10px;
    }
</style>
<div class="permanent-watermark">⚙️ System Core: Made by Niladri Das</div>
"""
st.markdown(watermark_layout, unsafe_allow_html=True)

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_role = None

SPREADSHEET_ID = "1ZKTLXv2VQEBG7OUeEo2GoF2Pz4IyYOot"

# --- API CONNECTION ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    try:
        return gspread.authorize(ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope))
    except Exception:
        creds_dict = st.secrets["gcp_service_account"]
        return gspread.authorize(ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope))

def load_sheet_data():
    client = get_gspread_client()
    sheet = client.open_by_key(SPREADSHEET_ID)
    all_data = []
    
    for wks in sheet.worksheets():
        name = wks.title.upper()
        if "_AT" in name:
            rake_id = name.split("_AT")[0].strip()
            side = "Alstom (AT)"
        elif "_RAIL" in name:
            rake_id = name.split("_RAIL")[0].strip()
            side = "Railway"
        else:
            continue
            
        records = wks.get_all_records()
        if records:
            df = pd.DataFrame(records)
            df.columns = [c.strip() for c in df.columns]
            df["Rake_ID"] = rake_id
            df["Side"] = side
            df["Sheet_Name"] = wks.title
            all_data.append(df)
            
    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        if "Status" not in combined.columns:
            combined["Status"] = "Open"
        return combined.drop_duplicates(subset=["Rake_ID", "Side", "Start time", "Event description"], keep="first")
    return pd.DataFrame()

# --- LOGIN POPUP GATEWAY ---
if not st.session_state.logged_in:
    st.title("🔒 System Access Required")
    with st.form("login_form"):
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            if user_id == "admin777" and password == "777":
                st.session_state.logged_in = True
                st.session_state.user_role = "Admin"
                st.success("Logged in as Admin")
                st.rerun()
            elif user_id == "user" and password == "999":
                st.session_state.logged_in = True
                st.session_state.user_role = "User"
                st.success("Logged in as User")
                st.rerun()
            else:
                st.error("Invalid credentials.")
    st.stop()

# --- LOAD DATA ---
try:
    df = load_sheet_data()
except Exception as e:
    st.error(f"Google Sheet Connection Error: {e}")
    st.stop()

# --- ENGINE ALGORITHM ---
def run_analysis_engine(data):
    if data.empty:
        return {"frequent": [], "unique": [], "rare": [], "major": []}
    
    counts = data["Event description"].value_counts()
    total = len(data)
    
    data["duration_min"] = pd.to_numeric(data["duration"], errors='coerce').fillna(0)
    major_faults = data.sort_values(by="duration_min", ascending=False).head(3)["Event description"].unique().tolist()
    
    return {
        "frequent": counts[counts > (total * 0.15)].index.tolist() or counts.head(2).index.tolist(),
        "unique": counts[counts == 1].index.tolist(),
        "rare": counts[(counts > 1) & (counts <= max(2, int(total * 0.05)))].index.tolist(),
        "major": major_faults
    }

# --- NAVIGATION SIDEBAR ---
st.sidebar.title(f"Portal ({st.session_state.user_role})")
menu = st.sidebar.radio("Menu Options", ["Rakes", "Overall Analysis", "Most Required Materials", "Update"])

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user_role = None
    st.rerun()

# Sidebar Watermark Backup
st.sidebar.markdown('<div class="sidebar-watermark">Application Architecture<br>© Made by Niladri Das</div>', unsafe_allow_html=True)

# --- NAVIGATION LOGIC ---
if menu == "Rakes":
    st.title("🚊 Rake Analysis Engine")
    
    rake_select = st.selectbox("Select Rake Number", sorted(df["Rake_ID"].unique()))
    side_select = st.radio("Select Division", ["Alstom (AT)", "Railway"])
    
    filtered = df[(df["Rake_ID"] == rake_select) & (df["Side"] == side_select)]
    
    if filtered.empty:
        st.info("No logs found for this selection.")
    else:
        metrics = run_analysis_engine(filtered)
        
        with st.expander("🔥 Frequent Faults", expanded=True):
            st.write(metrics["frequent"])
        with st.expander("💎 Unique Faults"):
            st.write(metrics["unique"])
        with st.expander("⚠️ Rare Faults"):
            st.write(metrics["rare"])
        with st.expander("🚨 Major Faults (Longest Duration)"):
            st.write(metrics["major"])
            
        st.subheader("Data Records")
        st.dataframe(filtered[["Start time", "end time", "duration", "Event description", "Location description", "Repair information", "Status"]], use_container_width=True)

elif menu == "Overall Analysis":
    st.title("📊 Fleet-Wide Analysis")
    col1, col2 = st.columns(2)
    with col1:
        st.plotly_chart(px.pie(df, names="Side", title="Fault Distribution"), use_container_width=True)
    with col2:
        st.plotly_chart(px.bar(df["Location description"].value_counts().head(10), title="Top 10 Fault Locations"), use_container_width=True)

elif menu == "Most Required Materials":
    st.title("🔧 Most Required Materials")
    all_text = " ".join(df["Repair information"].astype(str).lower())
    keywords = ["replaced", "changed", "card", "valve", "cable", "sensor", "fuse", "breaker"]
    hits = {kw.upper(): all_text.count(kw) for kw in keywords if all_text.count(kw) > 0}
    
    if hits:
        mat_df = pd.DataFrame(list(hits.items()), columns=["Material/Action", "Frequency"]).sort_values(by="Frequency", ascending=False)
        st.plotly_chart(px.bar(mat_df, x="Material/Action", y="Frequency", color="Frequency"), use_container_width=True)
    else:
        st.info("Insufficient breakdown data to extract material metrics.")

elif menu == "Update":
    st.title("⚙️ Update Section")
    if st.session_state.user_role != "Admin":
        st.error("Access Denied. Only admin777 can modify data records.")
    else:
        target_sheet = st.selectbox("Select Sheet Tab", sorted(df["Sheet_Name"].unique()))
        client = get_gspread_client()
        wks = client.open_by_key(SPREADSHEET_ID).worksheet(target_sheet)
        records = wks.get_all_records()
        
        if records:
            wks_df = pd.DataFrame(records)
            row_options = [f"Row {i+2}: {r.get('Event description','Unknown')} ({r.get('Start time')})" for i, r in wks_df.iterrows()]
            selected_row = st.selectbox("Select Line Item to Update", row_options)
            
            row_idx = row_options.index(selected_row) + 2
            headers = [h.strip() for h in wks.row_values(1)]
            
            if "Status" not in headers:
                wks.update_cell(1, len(headers) + 1, "Status")
                status_col = len(headers) + 1
            else:
                status_col = headers.index("Status") + 1
                
            current_status = wks.cell(row_idx, status_col).value or "Open"
            new_status = st.selectbox("Set Status", ["Open", "Closed"], index=0 if current_status == "Open" else 1)
            
            if st.button("Commit Changes to Google Sheet"):
                wks.update_cell(row_idx, status_col, new_status)
                st.success("Google Sheet updated! Clear cache or refresh to view changes.")
                st.cache_resource.clear()
