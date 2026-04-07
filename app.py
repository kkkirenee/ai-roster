import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from streamlit_calendar import calendar

# 1. 網頁頁面設定
st.set_page_config(page_title="班表自動辨識", layout="wide")

# 2. 安全讀取金鑰 (請確保在 Streamlit Secrets 設定中)
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    st.warning("⚠️ 請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FY"}

# --- CSS 終極黑化：月曆全深色、字體淺色、暖粉紅點綴 ---
st.markdown("""
    <style>
    /* 1. 全域背景：極致深黑 */
    .stApp, .main, .block-container { 
        background-color: #0e1117 !important; 
        color: #d1d5db !important; 
    }

    /* 2. 月曆組件深度黑化：強制覆蓋所有格子背景 */
    .fc, .fc-view-harness, .fc-scrollgrid, .fc-daygrid-body, .fc-scrollgrid-sync-table {
        background-color: #0e1117 !important;
    }
    .fc-daygrid-day {
        background-color: #0e1117 !important;
    }
    
    /* 徹底消滅「今日」標記 */
    .fc-day-today, .fc .fc-daygrid-day.fc-day-today {
        background-color: transparent !important;
        background: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* 3. 班號與格子樣式 */
    .fc-event-title { 
        font-size: 2.2rem !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        text-align: center !important; 
    }
    .fc-v-event, .fc-daygrid-event {
        background: #1c2128 !important;
        border-left: 4px solid #a2b5cd !important; /* 霧霾藍 */
        border-radius: 6px !important;
        min-height: 85px !important;
        margin: 4px !important;
        pointer-events: none !important;
    }
    
    /* 4. 日期數字與網格線 */
    .fc-daygrid-day-number { 
        font-size: 1.3rem !important; 
        font-weight: bold !important; 
        color: #8b949e !important; 
        padding: 12px !important; 
    }
    .fc-theme-standard td, .fc-theme-standard th { 
        border-color: #21262d !important; /* 極暗網格線 */
    }
    
    /* 5. 輸入框與按鈕：深黑背景 + 暖粉紅邊框 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1px solid #eabcc3 !important;
        border-radius: 8px !important;
    }
    div.stButton > button {
        background-color: #eabcc3 !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        width: 100% !important;
        height: 48px !important;
        border-radius: 10px !important;
    }

    /* 隱藏工具列與頁首頁尾 */
    .fc-toolbar { display: none !important; }
    header, footer { visibility: hidden; }
    [data-testid="stExpander"] { 
        border: 1px solid #30363d !important; 
        background-color: #0e1117 !important; 
    }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部功能區 (摺疊收納)
with st.expander("🛠️ 個人資訊與班表辨識"):
    c1, c2, c3, c4 = st.columns(4)
    with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
    with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
    with c3: u_fleet = st.selectbox("F", ["A321", "B738"], index=0, label_visibility="collapsed")
    with c4: u_rank = st.selectbox("R", ["FF", "FY"], index=1, label_visibility="collapsed")
    
    if st.button("💾 儲存資訊"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    st.markdown("<hr style='border-color: #30363d; opacity: 0.3;'>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if uploaded_file and st.button("🚀 執行 AI 辨識"):
        with st.spinner("正在辨識中..."):
            success = False
            models_to_try = ['gemini-1.5-flash', 'gemini-2.5-flash']
            for m_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name=m_name)
                    img = Image.open(uploaded_file)
                    prompt = "Return ONLY JSON: [{'title': '116', 'start': '2026-04-03'}]. April 2026."
                    response = model.generate_content([prompt, img])
                    clean_json = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if clean_json:
                        st.session_state.calendar_events = json.loads(clean_json.group())
                        success = True
                        break
                except: continue
            if success: st.rerun()
            else: st.error("辨識失敗")

# 5. 月曆上方：名牌 Banner
f = st.session_state.form_data
st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161b22 0%, #0e1117 100%); border-left: 5px solid #eabcc3; padding: 20px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #30363d;">
        <div style="font-size: 0.75rem; color: #a2b5cd; letter-spacing: 2px; margin-bottom: 8px; font-weight: bold;">CREW SCHEDULE SYSTEM</div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div style="font-size: 2rem; font-weight: 900; color: #f3f4f6;">
                {f["name"] if f["name"] else "待輸入姓名"} 
                <span style="font-size: 1.1rem; color: #8b949e; font-weight: normal; margin-left: 10px;">#{f["id"] if f["id"] else "------"}</span>
            </div>
            <div style="font-size: 1.1rem; color: #eabcc3; font-weight: bold; border: 1.5px solid #eabcc3; padding: 4px 12px; border-radius: 6px; background-color: rgba(234, 188, 195, 0.05);">
                {f["fleet"]} / {f["rank"]}
            </div>
        </div>
        <div style="font-size: 1.1rem; color: #6c7a89; margin-top: 12px; font-weight: bold; letter-spacing: 1px;">2026 APRIL</div>
    </div>
""", unsafe_allow_html=True)

# 6. 月曆顯示
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", 
    "initialDate": "2026-04-01", 
    "fixedWeekCount": False, 
    "aspectRatio": 0.8, 
    "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
