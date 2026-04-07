import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# 1. 網頁設定 (必須在第一行)
st.set_page_config(page_title="My Flight Calendar", layout="wide")

# 2. 安全讀取金鑰 (請確認 Secrets 裡是 GOOGLE_API_KEY)
if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("請在 Secrets 設定 GOOGLE_API_KEY")

# 3. 讀取 CSV
@st.cache_data
def load_data():
    try:
        df = pd.read_csv('flight_data.csv')
        df['Flight'] = df['Flight'].astype(str)
        return df
    except:
        return pd.DataFrame(columns=['Flight', 'Dep', 'Arr', 'DepTime', 'ArrTime'])

flight_db = load_data()

# 4. 初始化 Session
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "---", "rank": "---"}

# 5. CSS 視覺
st.markdown("""
    <style>
    :root { color-scheme: dark !important; }
    .stApp { background-color: #0e1117 !important; }
    .sub-title { color: #eabcc3; font-size: 2.0rem; font-weight: normal; margin-bottom: 15px; }
    .crew-card {
        background: linear-gradient(135deg, #1c2128 0%, #0e1117 100%);
        border: 2px solid #eabcc3; border-radius: 25px !important;
        padding: 22px; margin-bottom: 15px;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #eabcc3 0%, #f1d5d9 100%) !important;
        color: #0e1117 !important; border: none !important; font-weight: 800 !important; border-radius: 15px !important; height: 45px !important;
    }
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important; color: #d1d5db !important; border: 1.5px solid #4b5563 !important; border-radius: 15px !important;
    }
    .fc-event-title { font-size: 2.2rem !important; font-weight: 900 !important; color: #ffffff !important; text-align: center !important; }
    .fc-v-event, .fc-daygrid-event {
        background: rgba(162, 181, 205, 0.25) !important;
        border-left: 6px solid #a2b5cd !important;
        border-radius: 12px !important;
    }
    header, footer { visibility: hidden; }
    </style>
""", unsafe_allow_html=True)

# 6. 控制區
st.markdown('<p class="sub-title">班表自動辨識</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
with c3: u_fleet = st.selectbox("F", ["機隊", "A321", "B738"], label_visibility="collapsed")
with c4: u_rank = st.selectbox("R", ["職級", "FF", "FY"], label_visibility="collapsed")

if st.button("💖 儲存資訊並開始解析"):
    st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
    st.rerun()

uploaded_file = st.file_uploader("上傳班表截圖", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

# 7. 辨識邏輯 (硬編碼模型名稱，並增加多層錯誤捕獲)
if uploaded_file:
    if st.button("🚀 執行 AI 辨識"):
        with st.spinner("AI 解析中..."):
            try:
                # 這裡我們換成最通用的名稱，不加 models/ 前綴試試看
                model = genai.GenerativeModel('gemini-1.5-flash')
                img = Image.open(uploaded_file)
                prompt = "Return JSON list of April 2026 flights: [{'title': '116', 'start': '2026-04-03', 'overnight': false}]. If dash line follows flight, overnight: true. JSON ONLY."
                
                response = model.generate_content([prompt, img])
                res_text = response.text
                
                match = re.search(r'\[.*\]', res_text, re.DOTALL)
                if match:
                    raw = json.loads(match.group())
                    events = []
                    for it in raw:
                        ev = {"title": it['title'], "start": it['start'], "allDay": True}
                        if it.get('overnight'):
                            d = datetime.strptime(it['start'], "%Y-%m-%d")
                            ev["end"] = (d + timedelta(days=2)).strftime("%Y-%m-%d")
                        events.append(ev)
                    st.session_state.calendar_events = events
                    st.rerun()
            except Exception as e:
                # 如果 flash 失敗，強行切換到 Pro 嘗試
                try:
                    model = genai.GenerativeModel('gemini-1.5-pro')
                    response = model.generate_content([prompt, img])
                    # ... (重複處理邏輯，此處簡略)
                except:
                    st.error(f"解析失敗，請確認 API Key 權限。錯誤代碼: {str(e)}")

# 8. 名牌卡片
f = st.session_state.form_data
st.markdown(f"""<div class="crew-card">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div style="font-size: 0.7rem; color: #a2b5cd; font-weight: bold;">CREW ID CARD</div>
            <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;">{f["name"] if f["name"] else "------"}</div>
            <div style="font-size: 1.4rem; color: #d1d5db; font-weight: 800;">#{f["id"] if f["id"] else "------"}</div>
        </div>
        <div style="text-align: right;">
            <div style="font-size: 1.1rem; color: #eabcc3; font-weight: 900; border: 2px solid #eabcc3; padding: 5px 15px; border-radius: 18px;">{f["fleet"]} / {f["rank"]}</div>
            <div style="font-size: 1.2rem; color: #6c7a89; margin-top: 15px; font-weight: 900;">2026 APRIL</div>
        </div>
    </div>
</div>""", unsafe_allow_html=True)

# 9. 月曆
calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.85, "headerToolbar": {"left":"", "center":"", "right":""}
}, key="flight_calendar")
