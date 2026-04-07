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
    st.warning("⚠️ 請在 Streamlit Secrets 中設定 API KEY")

# 3. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    # 預設改為空值，讓使用者自行選擇
    st.session_state.form_data = {"name": "", "id": "", "fleet": "---", "rank": "---"}

# --- CSS 視覺重塑：圓潤名牌、大字員編、暖粉紅主題 ---
st.markdown("""
    <style>
    :root { color-scheme: dark !important; }
    .stApp { background-color: #0e1117 !important; }
    .main .block-container { padding-top: 1rem !important; }

    /* 名牌卡片：增加深度與圓角 */
    .crew-card {
        background: linear-gradient(135deg, #1c2128 0%, #0e1117 100%);
        border: 2px solid #eabcc3;
        border-radius: 25px !important;
        padding: 22px;
        margin-bottom: 15px;
        box-shadow: 0 10px 25px rgba(234, 188, 195, 0.15);
    }

    /* 輸入框與下拉選單 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important;
        color: #d1d5db !important;
        border: 1.5px solid #4b5563 !important;
        border-radius: 15px !important;
    }

    /* 圓潤按鈕：暖粉紅漸層 */
    div.stButton > button {
        background: linear-gradient(90deg, #eabcc3 0%, #f1d5d9 100%) !important;
        color: #0e1117 !important;
        border: none !important;
        font-weight: 800 !important;
        border-radius: 15px !important;
        height: 45px !important;
        box-shadow: 0 4px 12px rgba(234, 188, 195, 0.25);
    }

    /* 月曆大字體與黑底 */
    .fc { background-color: #0e1117 !important; border-radius: 20px !important; overflow: hidden; }
    .fc-event-title { font-size: 2.2rem !important; font-weight: 900 !important; color: #ffffff !important; text-align: center !important; }
    .fc-v-event, .fc-daygrid-event {
        background: rgba(162, 181, 205, 0.15) !important;
        border-left: 5px solid #a2b5cd !important;
        border-radius: 12px !important;
        min-height: 85px !important;
        margin: 4px !important;
    }
    
    .fc-daygrid-day-number { font-size: 1.2rem !important; color: #8b949e !important; padding: 10px !important; }
    .fc-day-today { background-color: transparent !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: #21262d !important; }
    .fc-toolbar, header, footer { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 功能控制區
st.markdown("<p style='color:#eabcc3; font-weight:bold; margin-bottom:5px; font-size:0.9rem;'>✨ 個人資訊設定</p>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
with c3: u_fleet = st.selectbox("F", ["請選擇機隊", "A321", "B738", "B777", "B787"], label_visibility="collapsed")
with c4: u_rank = st.selectbox("R", ["請選擇職級", "FF", "FY", "AP", "CP"], label_visibility="collapsed")

b1, b2 = st.columns([1, 2])
with b1:
    if st.button("💖 儲存資訊"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()
with b2:
    # 這裡改成中文標籤
    uploaded_file = st.file_uploader("上傳班表照片", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

if uploaded_file and st.button("🚀 開始自動辨識"):
    with st.spinner("AI 正在幫妳讀取班表... 🐾"):
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

st.markdown("<div style='margin-bottom: 20px;'></div>", unsafe_allow_html=True)

# 5. 月曆上方：高級圓潤名牌
f = st.session_state.form_data
st.markdown(f"""
    <div class="crew-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.7rem; color: #a2b5cd; letter-spacing: 2px; margin-bottom: 5px; font-weight: bold;">CREW ID CARD</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff; line-height: 1.2;">
                    {f["name"] if f["name"] != "" else "Irene"}
                </div>
                <div style="font-size: 1.4rem; color: #d1d5db; font-weight: 800; margin-top: 5px; letter-spacing: 1px;">
                    #{f["id"] if f["id"] != "" else "000000"}
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; color: #eabcc3; font-weight: 900; background: rgba(234, 188, 195, 0.1); padding: 8px 18px; border-radius: 18px; border: 2px solid #eabcc3; display: inline-block;">
                    {f["fleet"]} / {f["rank"]}
                </div>
                <div style="font-size: 1.2rem; color: #6c7a89; margin-top: 15px; font-weight: 900; letter-spacing: 1px;">
                    🗓️ 2026 APRIL
                </div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 6. 月曆顯示
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.85, "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
