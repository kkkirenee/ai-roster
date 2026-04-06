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

# 3. 初始化 Session State (確保初始全乾淨)
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FF"}

# --- CSS 高級配色優化：暖淺灰文字、霧霾藍標題、暖粉紅邊框 ---
st.markdown("""
    <style>
    /* 1. 全域背景與暖灰色文字：拒絕刺眼純白 */
    .stApp { 
        background-color: #0e1117 !important; 
        color: #d1d5db !important; /* 暖淺灰 */
    }
    .main .block-container { padding-top: 1rem !important; }
    
    /* 2. 徹底關閉「今日」所有特殊標記 */
    .fc-day-today, .fc-daygrid-day.fc-day-today, .fc .fc-daygrid-day.fc-day-today {
        background-color: transparent !important;
        background: none !important;
        box-shadow: none !important;
        border: none !important;
    }
    .fc .fc-daygrid-day.fc-day-today .fc-daygrid-day-number {
        background-color: transparent !important;
        border-radius: 0 !important;
    }

    /* 3. 班號與格子：霧霾藍側邊條 */
    .fc-event-title { 
        font-size: 2rem !important; 
        font-weight: 800 !important; 
        color: #f3f4f6 !important; /* 接近白的極淺灰 */
        text-align: center !important;
    }
    .fc-v-event, .fc-daygrid-event {
        background: #1c2128 !important;
        border-left: 3px solid #a2b5cd !important; /* 霧霾藍細線 */
        border-radius: 4px !important;
        min-height: 45px !important;
        margin: 2px !important;
        pointer-events: none !important;
    }
    
    /* 4. 日期數字：暖灰色文字 */
    .fc-daygrid-day-number { 
        font-size: 1.2rem !important; 
        font-weight: bold !important; 
        color: #9ca3af !important; 
        padding: 8px !important;
    }

    /* 5. 輸入框：深背景、暖粉紅細邊框 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1px solid #eabcc3 !important; /* 暖粉紅邊框 */
        padding: 2px 8px !important;
        font-size: 0.95rem !important;
    }
    
    /* 按鈕樣式：暖粉紅填充 */
    div.stButton > button {
        background-color: #eabcc3 !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: bold !important;
        width: 100% !important;
    }

    /* 網格線顏色調淡 */
    .fc-theme-standard td, .fc-theme-standard th { border-color: #21262d !important; }
    .fc-toolbar-title { display: none !important; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 4. 建立網頁排版
col_left, col_right = st.columns([1, 3])

with col_left:
    # 標題使用氣質霧霾藍
    st.markdown("<p style='font-size:1.2rem; font-weight:bold; color:#a2b5cd; margin-bottom:10px;'>班表自動辨識</p>", unsafe_allow_html=True)
    
    # 四欄並排 (全黑模式適配)
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        u_name = st.text_input("姓名", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
    with c2:
        u_id = st.text_input("員編", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
    with c3:
        u_fleet = st.selectbox("機隊", ["A321", "B738"], label_visibility="collapsed")
    with c4:
        u_rank = st.selectbox("職級", ["FF", "FY"], label_visibility="collapsed")

    if st.button("💾 儲存並同步"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    # 分隔線使用淡淡的暖粉紅
    st.markdown("<hr style='border-color: #eabcc3; opacity: 0.2; margin: 15px 0;'>", unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader("📷 上傳照片", type=['png', 'jpg', 'jpeg'], label_visibility="visible")
    if uploaded_file and st.button("🚀 執行 AI 辨識"):
        with st.spinner("辨識中..."):
            try:
                model = genai.GenerativeModel(model_name='gemini-2.5-flash')
                img = Image.open(uploaded_file)
                prompt = "Read schedule, return JSON: [{'title': '116', 'start': '2026-04-03'}]. Year 2026."
                response = model.generate_content([prompt, img])
                res_text = response.text.replace('```json', '').replace('```', '').strip()
                st.session_state.calendar_events = [ev for ev in json.loads(res_text) if "-04-" in ev['start']]
                st.rerun()
            except: st.error("辨識失敗")

with col_right:
    form_data = st.session_state.form_data
    # Banner 配色更新：暖粉紅底線 + 暖灰文字
    st.markdown(f"""
        <div style="border-bottom: 1.5px solid #eabcc3; padding-bottom: 8px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 1.1rem; font-weight: bold; color: #eabcc3;">2026 APRIL</div>
            <div style="display: flex; gap: 15px; font-size: 1rem; color: #d1d5db;">
                <span style="color:#f3f4f6; font-weight:bold;">{form_data["name"] if form_data["name"] else "---"}</span>
                <span>{form_data["id"] if form_data["id"] else "------"}</span>
                <span style="color:#a2b5cd;">{form_data["fleet"]} / {form_data["rank"]}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    calendar(events=st.session_state.calendar_events, options={
        "initialView": "dayGridMonth", 
        "initialDate": "2026-04-01", 
        "fixedWeekCount": False, 
        "aspectRatio": 2.2, 
        "headerToolbar": {"left":"", "center":"", "right":""}
    }, key="flight_calendar")
