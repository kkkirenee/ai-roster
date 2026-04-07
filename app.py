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
    st.error("請在 Streamlit Secrets 中設定 GOOGLE_API_KEY")

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FY"}

# --- CSS 視覺重塑：維持你的氣質暖粉霧霾藍 ---
st.markdown("""
    <style>
    .stApp { background-color: #0e1117 !important; }
    .main .block-container { padding-top: 1rem !important; padding-bottom: 2rem !important; }
    .fc-day-today, .fc .fc-daygrid-day.fc-day-today { background-color: transparent !important; border: none !important; }
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important; color: #d1d5db !important; border: 1px solid #eabcc3 !important; border-radius: 6px !important;
    }
    div.stButton > button {
        background-color: #eabcc3 !important; color: #0e1117 !important; border: none !important; font-weight: bold !important; width: 100% !important; height: 45px !important; border-radius: 8px !important;
    }
    .fc-event-title { font-size: 2.2rem !important; font-weight: 900 !important; color: #ffffff !important; text-align: center !important; }
    .fc-v-event, .fc-daygrid-event { background: #1c2128 !important; border-left: 4px solid #a2b5cd !important; border-radius: 4px !important; min-height: 80px !important; margin: 3px !important; pointer-events: none !important; }
    .fc-daygrid-day-number { font-size: 1.3rem !important; font-weight: bold !important; color: #9ca3af !important; padding: 10px !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: #262c33 !important; }
    .fc-toolbar { display: none !important; }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# 4. 頂部功能區 (摺疊設定)
with st.expander("🛠️ 設定資訊與辨識照片"):
    c1, c2, c3, c4 = st.columns(4)
    with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
    with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
    with c3: u_fleet = st.selectbox("F", ["A321", "B738"], index=0, label_visibility="collapsed")
    with c4: u_rank = st.selectbox("R", ["FF", "FY"], index=1, label_visibility="collapsed")
    
    if st.button("💾 儲存並更新名牌"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    st.markdown("---")
    uploaded_file = st.file_uploader("Upload", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")
    if uploaded_file and st.button("🚀 執行 AI 辨識"):
        with st.spinner("正在嘗試多個 AI 模型進行辨識..."):
            success = False
            # 輪流嘗試不同的模型，避開額度限制
            models_to_try = ['gemini-2.5-flash', 'gemini-1.5-flash', 'gemini-1.5-pro-002']
            
            for m_name in models_to_try:
                try:
                    model = genai.GenerativeModel(model_name=m_name)
                    img = Image.open(uploaded_file)
                    prompt = "Analyze schedule. Return ONLY JSON list: [{'title': '116', 'start': '2026-04-03'}]. Limit April 2026."
                    response = model.generate_content([prompt, img])
                    clean_json = re.search(r'\[.*\]', response.text, re.DOTALL)
                    if clean_json:
                        st.session_state.calendar_events = json.loads(clean_json.group())
                        success = True
                        break # 成功就跳出迴圈
                except Exception as e:
                    continue # 失敗就試下一個
            
            if success:
                st.rerun()
            else:
                st.error("所有 AI 模型額度皆已用完，請稍後再試或更換 API Key。")

# 5. 月曆上方：名牌 Banner
f = st.session_state.form_data
st.markdown(f"""
    <div style="background: linear-gradient(90deg, #161b22 0%, #0e1117 100%); border-left: 5px solid #eabcc3; padding: 15px; margin-bottom: 10px; border-radius: 4px; border-bottom: 1px solid #30363d;">
        <div style="font-size: 0.75rem; color: #a2b5cd; letter-spacing: 1.5px; margin-bottom: 5px;">CREW SCHEDULE REPORT</div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="font-size: 1.8rem; font-weight: 900; color: #f3f4f6;">
                {f["name"] if f["name"] else "尚未輸入"} <span style="font-size: 1rem; color: #9ca3af; font-weight: normal;">({f["id"] if f["id"] else "NO ID"})</span>
            </div>
            <div style="font-size: 1.1rem; color: #eabcc3; font-weight: bold; border: 1px solid #eabcc3; padding: 2px 8px; border-radius: 4px;">
                {f["fleet"]} / {f["rank"]}
            </div>
        </div>
        <div style="font-size: 1rem; color: #6c7a89; margin-top: 8px; font-weight: bold;">2026 APRIL</div>
    </div>
""", unsafe_allow_html=True)

# 6. 月曆顯示
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.85, "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
