import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from streamlit_calendar import calendar

# 1. 網頁頁面設定：深色、極簡
st.set_page_config(page_title="班表自動辨識", layout="wide")

# 2. 設定 AI 金鑰
GOOGLE_API_KEY = 'AIzaSyDtSZ5C8fAkPo6lsCMkayK-Gh6VqTH_FeU'
genai.configure(api_key=GOOGLE_API_KEY)

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FF"}

# --- CSS 終極瘦身優化：格子變小、文字居中、移除點選手感 ---
st.markdown("""
    <style>
    /* 強制深色 */
    .stApp { background-color: #0e1117 !important; color: #ffffff !important; }
    .main .block-container { padding-top: 1rem !important; }
    
    /* 1. 今日(7號) 霧霾藍焦點：更淡更細 */
    .fc-day-today, .fc-daygrid-day.fc-day-today {
        background-color: rgba(108, 122, 137, 0.1) !important; 
        border: 1px solid rgba(108, 122, 137, 0.3) !important; 
    }

    /* 2. 班號字體微調：保持大字但增加空間感 */
    .fc-event-title { 
        font-size: 1.8rem !important; 
        font-weight: 800 !important; 
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* 3. 格子瘦身：大幅縮減 min-height，讓格子變窄 */
    .fc-v-event, .fc-daygrid-event {
        background: #1a1a1a !important;
        border-left: 3px solid #6c7a89 !important; 
        border-radius: 3px !important;
        min-height: 40px !important; /* 從 60 縮減到 40，格子變扁 */
        margin: 2px !important;
        cursor: default !important; /* 移除點選的手指符號 */
        pointer-events: none !important; /* 徹底停用所有點選與懸停事件 */
    }
    
    /* 4. 日期數字：縮小一點 1.2rem */
    .fc-daygrid-day-number { 
        font-size: 1.2rem !important; 
        font-weight: bold !important; 
        color: #888 !important; 
    }

    /* 5. 輸入框：霧霾藍極細線 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #1a1a1a !important;
        border: 1px solid #6c7a89 !important; 
    }
    
    /* 網格線變淡 */
    .fc-theme-standard td, .fc-theme-standard th { border-color: #222222 !important; }
    .fc-toolbar-title { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 建立網頁排版
col_left, col_right = st.columns([0.8, 3])

with col_left:
    st.markdown("<p style='font-size:1.3rem; font-weight:bold; color:#a2b5cd; margin-bottom:10px;'>班表自動辨識</p>", unsafe_allow_html=True)
    
    # 資訊設定：兩兩一組
    r1_c1, r1_c2 = st.columns(2)
    with r1_c1:
        u_name = st.text_input("姓名", value=st.session_state.form_data["name"], placeholder="姓名")
    with r1_c2:
        u_id = st.text_input("員編", value=st.session_state.form_data["id"], placeholder="員編")
        
    r2_c1, r2_c2 = st.columns(2)
    with r2_c1:
        u_fleet = st.selectbox("機隊", ["A321", "B738"])
    with r2_c2:
        u_rank = st.selectbox("職級", ["FF", "FY"])

    if st.button("💾 儲存同步"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    st.markdown("---")
    uploaded_file = st.file_uploader("📷 上傳照片", type=['png', 'jpg', 'jpeg'])
    if uploaded_file and st.button("🚀 AI 辨識"):
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
    # Banner 排版優化
    st.markdown(f"""
        <div style="border-bottom: 1.5px solid #6c7a89; padding-bottom: 8px; margin-bottom: 15px; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center;">
            <div style="font-size: 1.2rem; font-weight: bold; color: white;">2026 APRIL</div>
            <div style="display: flex; gap: 15px; font-size: 1rem; color: #ccc;">
                <span>{form_data["name"] if form_data["name"] else "---"}</span>
                <span>{form_data["id"] if form_data["id"] else "------"}</span>
                <span style="color:#a2b5cd;">{form_data["fleet"]} / {form_data["rank"]}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 渲染月曆：調高 aspectRatio 讓格子變「扁」，移除所有互動
    calendar(events=st.session_state.calendar_events, options={
        "initialView": "dayGridMonth", 
        "initialDate": "2026-04-01", 
        "fixedWeekCount": False, 
        "aspectRatio": 2.2, # 數字越大，格子越扁平
        "headerToolbar": {"left":"", "center":"", "right":""},
        "editable": False,
        "selectable": False
    }, key="flight_calendar")
