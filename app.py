import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from streamlit_calendar import calendar

# 1. 網頁頁面設定
st.set_page_config(page_title="班表自動辨識", layout="wide")

# 2. 設定 AI 金鑰
GOOGLE_API_KEY = 'AIzaSyDtSZ5C8fAkPo6lsCMkayK-Gh6VqTH_FeU'
genai.configure(api_key=GOOGLE_API_KEY)

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FF"}

# --- CSS 終極黑化 + 手機高度壓縮 ---
st.markdown("""
    <style>
    /* 1. 全域背景全黑 */
    .stApp, .main, .block-container { 
        background-color: #0e1117 !important; 
        color: #d1d5db !important; 
        padding-top: 0.5rem !important;
    }
    
    /* 2. 上傳區塊黑化 */
    div[data-testid="stFileUploadDropzone"] {
        background-color: #161b22 !important;
        border: 1px dashed #6c7a89 !important;
    }
    div[data-testid="stFileUploader"] section {
        background-color: #161b22 !important;
    }

    /* 3. 輸入框與選單黑化 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #0e1117 !important;
        color: #d1d5db !important;
        border: 1px solid #eabcc3 !important;
        height: 35px !important;
    }

    /* 4. 月曆高度極限壓縮 (讓手機不用捲動) */
    .fc-v-event, .fc-daygrid-event {
        background: #1c2128 !important;
        border-left: 2px solid #a2b5cd !important;
        min-height: 28px !important; /* 超扁平格子 */
        margin: 1px !important;
    }
    .fc-event-title { 
        font-size: 1.4rem !important; /* 縮小一點點以適應扁平格子 */
        color: #ffffff !important;
    }
    .fc-daygrid-day-number { 
        font-size: 1rem !important; 
        padding: 2px 5px !important;
    }
    
    /* 5. 徹底隱藏今日標記與日曆標題 */
    .fc-day-today { background-color: transparent !important; }
    .fc-toolbar, .fc-header-toolbar { display: none !important; }
    header, footer { visibility: hidden; height: 0; }
    
    /* 6. 按鈕暖粉紅 */
    div.stButton > button {
        background-color: #eabcc3 !important;
        color: #0e1117 !important;
        border: none !important;
        height: 35px !important;
        padding: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部控制區 (四欄並排，高度極小化)
c1, c2, c3, c4 = st.columns(4)
with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
with c3: u_fleet = st.selectbox("F", ["A321", "B738"], label_visibility="collapsed")
with c4: u_rank = st.selectbox("R", ["FF", "FY"], label_visibility="collapsed")

# 按鈕與上傳併排 (節省高度)
b1, b2 = st.columns([1, 2])
with b1:
    if st.button("💾 儲存"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()
with b2:
    uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if uploaded_file:
    if st.button("🚀 AI 辨識班表"):
        with st.spinner("辨識中..."):
            try:
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                img = Image.open(uploaded_file)
                prompt = "Read schedule, return JSON: [{'title': '116', 'start': '2026-04-03'}]. Year 2026."
                response = model.generate_content([prompt, img])
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.calendar_events = [ev for ev in json.loads(res_text) if "-04-" in ev['start']]
                st.rerun()
            except: st.error("失敗")

# 5. 月曆顯示區
form_data = st.session_state.form_data
st.markdown(f"""
    <div style="border-bottom: 1px solid #eabcc3; padding: 2px 0; margin-bottom: 10px; display: flex; justify-content: space-between; font-size: 0.9rem; color: #d1d5db;">
        <span><b>2026 APR</b> | {form_data["name"] if form_data["name"] else "---"}</span>
        <span style="color:#a2b5cd;">{form_data["fleet"]} {form_data["rank"]}</span>
    </div>
""", unsafe_allow_html=True)

# aspectRatio 設為 2.8-3.0，格子會變得很扁，確保手機螢幕能塞下全月
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", 
    "initialDate": "2026-04-01", 
    "fixedWeekCount": False, 
    "aspectRatio": 3.0, 
    "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
