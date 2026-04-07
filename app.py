import streamlit as st
from PIL import Image
import google.generativeai as genai
import json
import pandas as pd
import re
from datetime import datetime, timedelta
from streamlit_calendar import calendar

# 1. 網頁設定
st.set_page_config(page_title="My Flight Calendar", layout="wide")

# 2. 安全讀取金鑰
try:
    GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=GOOGLE_API_KEY)
except:
    st.warning("⚠️ 請在 Streamlit Secrets 中設定 API KEY")

# --- 3. 讀取 CSV 資料 (請確保 GitHub 內有 flight_data.csv) ---
@st.cache_data
def load_flight_data():
    try:
        # 假設 CSV 欄位: Flight, Dep, Arr, DepTime, ArrTime
        df = pd.read_csv('flight_data.csv')
        df['Flight'] = df['Flight'].astype(str)
        return df
    except:
        # 如果沒檔案，先給空表避免報錯
        return pd.DataFrame(columns=['Flight', 'Dep', 'Arr', 'DepTime', 'ArrTime'])

flight_db = load_flight_data()

# 報到時間計算
def calculate_checkin(dep_airport, dep_time_str):
    try:
        t = datetime.strptime(dep_time_str, "%H:%M")
        if dep_airport == "TPE":
            checkin = t - timedelta(minutes=140)
        elif dep_airport == "TSA":
            checkin = t - timedelta(minutes=90)
        else:
            checkin = t - timedelta(hours=2)
        return checkin.strftime("%H:%M")
    except:
        return "--:--"

# 4. 初始化 Session State
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "---", "rank": "---"}

# --- CSS 視覺重塑 ---
st.markdown("""
    <style>
    :root { color-scheme: dark !important; }
    .stApp { background-color: #0e1117 !important; }
    .sub-title { color: #eabcc3; font-size: 2.0rem; font-weight: normal; margin-bottom: 10px; }
    
    .crew-card {
        background: linear-gradient(135deg, #1c2128 0%, #0e1117 100%);
        border: 2px solid #eabcc3;
        border-radius: 25px !important;
        padding: 22px; margin-bottom: 15px;
        box-shadow: 0 10px 25px rgba(234, 188, 195, 0.15);
    }
    
    .detail-card {
        background: #1c2128; border-radius: 20px; padding: 25px; margin-top: 20px;
        border: 1.5px solid #eabcc3; box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    .info-row { display: flex; justify-content: space-between; margin-bottom: 15px; border-bottom: 1px solid #30363d; padding-bottom: 8px; }
    .info-label { color: #8b949e; font-size: 0.85rem; }
    .info-value { color: #ffffff; font-weight: bold; font-size: 1.1rem; }
    .checkin-highlight { color: #eabcc3; font-size: 1.5rem; font-weight: 900; }

    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        background-color: #161b22 !important; color: #d1d5db !important; border: 1.5px solid #4b5563 !important; border-radius: 15px !important;
    }
    div.stButton > button {
        background: linear-gradient(90deg, #eabcc3 0%, #f1d5d9 100%) !important;
        color: #0e1117 !important; border: none !important; font-weight: 800 !important; border-radius: 15px !important; height: 45px !important;
    }
    .fc { background-color: #0e1117 !important; border-radius: 20px !important; overflow: hidden; }
    .fc-event-title { font-size: 2.2rem !important; font-weight: 900 !important; color: #ffffff !important; text-align: center !important; }
    .fc-v-event, .fc-daygrid-event {
        background: rgba(162, 181, 205, 0.25) !important;
        border-left: 6px solid #a2b5cd !important;
        border-radius: 12px !important; min-height: 85px !important; margin: 4px !important;
    }
    .fc-daygrid-day-number { font-size: 1.2rem !important; color: #8b949e !important; padding: 10px !important; }
    .fc-theme-standard td, .fc-theme-standard th { border-color: #21262d !important; }
    .fc-toolbar, header, footer { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# 5. 功能控制區
st.markdown('<p class="sub-title">班表自動辨識</p>', unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)
with c1: u_name = st.text_input("N", value=st.session_state.form_data["name"], placeholder="姓名", label_visibility="collapsed")
with c2: u_id = st.text_input("I", value=st.session_state.form_data["id"], placeholder="員編", label_visibility="collapsed")
with c3: u_fleet = st.selectbox("機隊", ["機隊", "A321", "B738"], label_visibility="collapsed")
with c4: u_rank = st.selectbox("職級", ["職級", "FF", "FY"], label_visibility="collapsed")

b1, b2 = st.columns([1, 2])
with b1:
    if st.button("💖 儲存資訊"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()
with b2:
    uploaded_file = st.file_uploader("上傳班表", type=['png', 'jpg', 'jpeg'], label_visibility="collapsed")

# --- 6. 核心辨識邏輯：處理過夜班橫槓 ---
if uploaded_file and st.button("🚀 開始自動辨識"):
    with st.spinner("正在讀取 4 月班表... 🐾"):
        try:
            model = genai.GenerativeModel(model_name='gemini-1.5-flash')
            img = Image.open(uploaded_file)
            prompt = """
            妳是專業空服員班表助手。請讀取圖中 2026年4月的航班。
            注意：
            1. 只抓粉紅色的大數字班號。忽略小字的農曆和Rdo。
            2. 如果班號後方有橫線（如 150—），代表這是過夜班，請標註為 "overnight": true。
            3. 回傳格式為 JSON 列表：
               [{"title": "116", "start": "2026-04-03", "overnight": false}, 
                {"title": "150", "start": "2026-04-12", "overnight": true}]
            """
            response = model.generate_content([prompt, img])
            match = re.search(r'\[.*\]', response.text, re.DOTALL)
            if match:
                raw_data = json.loads(match.group())
                events = []
                for item in raw_data:
                    ev = {
                        "title": item['title'],
                        "start": item['start'],
                        "allDay": True
                    }
                    if item.get("overnight"):
                        # 如果是過夜班，結束時間設為隔天，月曆就會顯示一槓到底
                        start_dt = datetime.strptime(item['start'], "%Y-%m-%d")
                        ev["end"] = (start_dt + timedelta(days=2)).strftime("%Y-%m-%d")
                    events.append(ev)
                st.session_state.calendar_events = events
                st.rerun()
        except: st.error("辨識失敗，請再試一次")

# 7. 名牌卡片
f = st.session_state.form_data
st.markdown(f"""
    <div class="crew-card">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <div style="font-size: 0.7rem; color: #a2b5cd; letter-spacing: 2px; font-weight: bold;">CREW ID CARD</div>
                <div style="font-size: 1.8rem; font-weight: 900; color: #ffffff;">{f["name"] if f["name"] else "------"}</div>
                <div style="font-size: 1.4rem; color: #d1d5db; font-weight: 800; margin-top: 5px;">#{f["id"] if f["id"] else "------"}</div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 1.1rem; color: #eabcc3; font-weight: 900; border: 2px solid #eabcc3; padding: 5px 15px; border-radius: 18px;">{f["fleet"]} / {f["rank"]}</div>
                <div style="font-size: 1.2rem; color: #6c7a89; margin-top: 15px; font-weight: 900;">🗓️ 2026 APRIL</div>
            </div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 8. 月曆顯示
cal_result = calendar(events=st.session_state.calendar_events, options={
    "initialView": "dayGridMonth", "initialDate": "2026-04-01", "fixedWeekCount": False, "aspectRatio": 0.85, "headerToolbar": {"left":"", "center":"", "right":""},
    "selectable": True,
}, key="flight_calendar")

# 9. 航班詳細資訊（去回程整合）
if cal_result.get("eventClick"):
    flight_no = cal_result["eventClick"]["event"]["title"]
    outbound = flight_db[flight_db['Flight'] == str(flight_no)]
    
    if not outbound.empty:
        row = outbound.iloc[0]
        # 尋找回程 (通常是 +1)
        inbound_no = str(int(flight_no) + 1)
        inbound = flight_db[flight_db['Flight'] == inbound_no]
        checkin_t = calculate_checkin(row['Dep'], row['DepTime'])
        
        st.markdown(f"""
            <div class="detail-card">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <div style="font-size: 2rem; font-weight:
