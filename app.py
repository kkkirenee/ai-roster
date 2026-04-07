import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from streamlit_calendar import calendar

# 1. 網頁頁面設定
st.set_page_config(page_title="My Flight Calendar", layout="wide")

# 2. 安全讀取金鑰
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    st.warning("⚠️ 請設定 API KEY")

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FY"}

# --- CSS 可愛圓潤調校：超大圓角、暖粉紅陰影、強制黑底 ---
st.markdown("""
    <style>
    /* 全域深色與可愛字體感 */
    :root { color-scheme: dark !important; }
    .stApp { background-color: #0e1117 !important; font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }
    .main .block-container { padding-top: 1rem !important; }

    /* 1. 名牌 Banner：超圓潤可愛感 */
    .crew-card {
        background: linear-gradient(135deg, #1c2128 0%, #0e1117 100%);
        border: 2px solid #eabcc3;
        border-radius: 25px !important;
        padding: 20px;
        margin-bottom: 15px;
        box-shadow: 0 8px 20px rgba(234, 188, 195, 0.15);
    }

    /* 2. 輸入框與按鈕：圓滾滾造型 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1.5px solid #6c7a89 !important;
        border-radius: 15px !important;
        height: 40px !important;
    }
    input[type="text"]:focus { border-color: #eabcc3 !important; }

    div.stButton > button {
        background: linear-gradient(90deg, #eabcc3 0%, #f1d5d9 100%) !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        height: 45px !important;
        box-shadow: 0 4px 10px rgba(234, 188, 195, 0.3);
    }

    /* 3. 月曆深度黑化與圓角 */
    .fc { 
        background-color: #0e1117 !important; 
        border-radius: 20px !important; 
        overflow: hidden !important; 
    }
    .fc-view-harness, .fc-scrollgrid, .fc-daygrid-day { background-color: #0e1117 !important; }
    
    /* 班號格子：也要圓圓的 */
    .fc-event-title { 
        font-size: 2.2rem !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        text-align: center !important; 
    }
    .fc-v-event, .fc-daygrid-event {
        background: rgba(162, 181, 205, 0.2) !important; /* 霧霾藍半透明 */
        border-left: 5px solid #a2b5cd !important;
        border-radius: 12px !important;
        min-height: 85px !important;
        margin: 4px !important;
    }
    
    /* 日期數字：可愛灰 */
    .fc-daygrid-day-number { font-size: 1.2rem !important; color: #8b949e !important; padding: 10px !important; }
    
    /* 徹底消滅今日標記 */
    .fc-day-today { background-color: transparent !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: #21262d !important; }
    .fc-toolbar, header, footer { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部功能區 (不再隱藏，改為橫向可愛排版)
st.markdown("<p style='color:#eabcc3; font-weight:bold; margin-bottom:5px; font-size:0.9rem;'>✨ 班表小助手</p>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="名字", label_visibility="collapsed")
with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
with c3: u_fleet = st.selectbox("F", ["A321", "B738"], index=0, label_visibility="collapsed")
with c4: u_rank = st.selectbox("R", ["FF", "FY"], index=1, label_visibility="collapsed")

b1, b2 = st.columns([1, 2])
with b1:
    if st.button("💖 儲存資訊"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()
with b2:
    uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if uploaded_file and st.button("🚀 開始辨識照片"):
    with st.spinner("AI 正在幫妳看班表... 🐾"):
        success = False
        for m_name in ['gemini-1.5-flash', 'gemini-2.5-flash']:
            try:
                model = genai.GenerativeModel(model_name=m_name)
                img = Image.open(uploaded_file)
                prompt = "Return ONLY JSON: [{'title': '116', 'start': '2026-04-03'}]. April 2026."
                response = model.generate_content([prompt, img])
                clean_json = re.search(r'\[.*\]', response.text, re.DOTALL)
                if clean_json:
                    st.session_state.calendar_events = json.loads(clean_json.group())
                    success = True; break
            except: continue
        if success: st.rerun()

st.markdown("<div style='margin-bottom: 25px;'></div>", unsafe_allow_html=True)

# 5. 月曆上方：可愛名牌 Banner
f = st.session_state.form_data
st.markdown(f"""
    <div class="crew-card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 0.7rem; color: #a2b5cd; letter-spacing: 2px; margin-bottom: 5px;">FLIGHT CREW</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #f3f4f6;">
                    {f["name"] if f["name"] else "Irene"} <span style="font-size: 0.9rem; color: #8b949e; font-weight: normal;">#{f["id"] if f["id"] else "000000"}</span>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1rem; color: #eabcc3; font-weight: 800; background: rgba(234, 188, 195, 0.1); padding: 5px 15px; border-radius: 15px; border: 1.5px solid #eabcc3;">
                    {f["fleet"]} / {f["rank"]}
                </div>
            </div>
        </div>
        <div style="font-size: 1.1rem; color: #6c7a89; margin-top: 15px; font-weight: 800;">🗓️ 2026 APRIL</div>
    </div>
""", unsafe_allow_html=True)

# 6. 月曆顯示
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.85, "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
