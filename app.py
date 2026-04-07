import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from streamlit_calendar import calendar

# 1. 網頁頁面設定
st.set_page_config(page_title="班表自動辨識", layout="wide")

# 2. 安全讀取金鑰
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

# --- CSS 終極黑化：針對手機瀏覽器強化強制覆蓋 ---
st.markdown("""
    <style>
    /* 1. 強制全域深色 */
    :root { color-scheme: dark !important; }
    
    .stApp, .main, .block-container, [data-testid="stVerticalBlock"] { 
        background-color: #0e1117 !important; 
        color: #d1d5db !important; 
    }

    /* 2. 月曆組件：每一層都強制黑底 */
    iframe { background-color: #0e1117 !important; } /* 關鍵：月曆是以 iframe 渲染的 */
    
    .fc, .fc-view-harness, .fc-scrollgrid, .fc-daygrid-body, .fc-day, .fc-daygrid-day-frame {
        background-color: #0e1117 !important;
        background: #0e1117 !important;
    }
    
    /* 徹底移除今日(7號)標記與底色 */
    .fc-day-today, .fc .fc-daygrid-day.fc-day-today, .fc-daygrid-day.fc-day-today .fc-daygrid-day-frame {
        background-color: transparent !important;
        background: none !important;
        box-shadow: none !important;
        border: none !important;
    }

    /* 3. 航班格子與字體 */
    .fc-event-title { 
        font-size: 2.2rem !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        text-align: center !important; 
    }
    .fc-v-event, .fc-daygrid-event, .fc-event-main {
        background: #1c2128 !important;
        background-color: #1c2128 !important;
        border-left: 4px solid #a2b5cd !important;
        border-radius: 6px !important;
        min-height: 85px !important;
    }
    
    /* 4. 日期數字與網格線 */
    .fc-daygrid-day-number { 
        font-size: 1.3rem !important; 
        font-weight: bold !important; 
        color: #8b949e !important; 
    }
    .fc-theme-standard td, .fc-theme-standard th, .fc-scrollgrid { 
        border-color: #262c33 !important; 
    }
    
    /* 5. 輸入框與按鈕 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1px solid #eabcc3 !important;
    }
    div.stButton > button {
        background-color: #eabcc3 !important;
        color: #0e1117 !important;
        font-weight: bold !important;
        height: 48px !important;
        border-radius: 10px !important;
    }

    /* 隱藏組件 */
    .fc-toolbar, header, footer { display: none !important; visibility: hidden; }
    [data-testid="stExpander"] { background-color: #0e1117 !important; border: 1px solid #30363d !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部摺疊區
with st.expander("🛠️ 設定資訊與辨識"):
    c1, c2, c3, c4 = st.columns(4)
    with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
    with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
    with c3: u_fleet = st.selectbox("F", ["A321", "B738"], index=0, label_visibility="collapsed")
    with c4: u_rank = st.selectbox("R", ["FF", "FY"], index=1, label_visibility="collapsed")
    
    if st.button("💾 儲存資訊"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if uploaded_file and st.button("🚀 執行 AI 辨識"):
        with st.spinner("辨識中..."):
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
                        success = True
                        break
                except: continue
            if success: st.rerun()
            else: st.error("辨識失敗")

# 5. 名牌 Banner
f = st.session_state.form_data
st.markdown(f"""
    <div style="background: linear-gradient(135deg, #161b22 0%, #0e1117 100%); border-left: 5px solid #eabcc3; padding: 20px; margin-bottom: 10px; border-radius: 8px; border: 1px solid #30363d;">
        <div style="font-size: 0.75rem; color: #a2b5cd; letter-spacing: 2px; margin-bottom: 8px; font-weight: bold;">CREW SCHEDULE SYSTEM</div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div style="font-size: 2rem; font-weight: 900; color: #f3f4f6;">
                {f["name"] if f["name"] else "尚未輸入"} 
                <span style="font-size: 1.1rem; color: #8b949e; font-weight: normal; margin-left: 10px;">#{f["id"] if f["id"] else "------"}</span>
            </div>
            <div style="font-size: 1.1rem; color: #eabcc3; font-weight: bold; border: 1.5px solid #eabcc3; padding: 4px 12px; border-radius: 6px; background-color: rgba(234, 188, 195, 0.05);">
                {f["fleet"]} / {f["rank"]}
            </div>
        </div>
        <div style="font-size: 1.1rem; color: #6c7a89; margin-top: 12px; font-weight: bold;">2026 APRIL</div>
    </div>
""", unsafe_allow_html=True)

# 6. 月曆顯示
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.8, "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
