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
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FY"}

# --- CSS 視覺重塑：回歸大氣、字體清晰、自然捲動 ---
st.markdown("""
    <style>
    /* 全域背景全黑 */
    .stApp { background-color: #0e1117 !important; }
    .main .block-container { padding-top: 1.5rem !important; padding-bottom: 2rem !important; }

    /* 1. 今日(7號) 徹底透明化 */
    .fc-day-today, .fc .fc-daygrid-day.fc-day-today {
        background-color: transparent !important;
        background: none !important;
        box-shadow: none !important;
        border: none !important;
    }
    
    /* 2. 輸入框與選單：暖粉紅細邊 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1px solid #eabcc3 !important;
        border-radius: 6px !important;
    }

    /* 3. 儲存按鈕：大氣、滿版、暖粉紅 */
    div.stButton > button {
        background-color: #eabcc3 !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        width: 100% !important;
        height: 50px !important;
        border-radius: 8px !important;
    }

    /* 4. 月曆質感：回歸大格子、霸氣班號 */
    .fc-event-title { 
        font-size: 2.2rem !important; /* 班號就是要大！ */
        font-weight: 900 !important; 
        color: #ffffff !important;
        text-align: center !important;
        padding-top: 5px !important;
    }
    .fc-v-event, .fc-daygrid-event {
        background: #1c2128 !important;
        border-left: 4px solid #a2b5cd !important;
        border-radius: 4px !important;
        min-height: 80px !important; /* 增加高度，讓格子撐開 */
        margin: 3px !important;
        pointer-events: none !important;
    }
    
    /* 日期數字：暖灰色，清晰易讀 */
    .fc-daygrid-day-number { 
        font-size: 1.3rem !important; 
        font-weight: bold !important; 
        color: #9ca3af !important; 
        padding: 10px !important;
    }
    
    /* 網格線條 */
    .fc-theme-standard td, .fc-theme-standard th { border-color: #262c33 !important; }
    .fc-toolbar { display: none !important; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部資訊 Banner
form_data = st.session_state.form_data
st.markdown(f"""
    <div style="display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 20px; border-bottom: 2px solid #eabcc3; padding-bottom: 8px;">
        <div style="font-size: 1.6rem; font-weight: bold; color: #eabcc3;">2026 APRIL</div>
        <div style="font-size: 1rem; color: #d1d5db;">
            <b style="color:white;">{form_data["name"] if form_data["name"] else "尚未輸入"}</b> | {form_data["fleet"]} {form_data["rank"]}
        </div>
    </div>
""", unsafe_allow_html=True)

# 輸入區：2x2 排列
c1, c2 = st.columns(2)
with c1:
    u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
    u_fleet = st.selectbox("F", ["A321", "B738"], index=0, label_visibility="collapsed")
with c2:
    u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
    u_rank = st.selectbox("R", ["FF", "FY"], index=1, label_visibility="collapsed")

if st.button("💾 儲存更新資訊"):
    st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
    st.rerun()

st.markdown("---")

# 上傳區塊
uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
if uploaded_file and st.button("🚀 執行辨識"):
    with st.spinner("AI 分析中..."):
        try:
            model = genai.GenerativeModel(model_name='gemini-2.5-flash')
            img = Image.open(uploaded_file)
            prompt = "Read schedule, return JSON: [{'title': '116', 'start': '2026-04-03'}]. Year 2026."
            response = model.generate_content([prompt, img])
            res_text = response.text.replace('```json', '').replace('```', '').strip()
            st.session_state.calendar_events = [ev for ev in json.loads(res_text) if "-04-" in ev['start']]
            st.rerun()
        except: st.error("失敗")

# 5. 月曆顯示：大氣捲動模式
# aspectRatio 設為 0.8 或 0.9，這會讓格子變高。
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", 
    "initialDate": "2026-04-01", 
    "fixedWeekCount": False, 
    "aspectRatio": 0.85, 
    "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
