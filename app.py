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

# 3. 初始化 Session State (確保初始為全乾淨狀態)
if 'calendar_events' not in st.session_state:
    st.session_state.calendar_events = []
if 'form_data' not in st.session_state:
    st.session_state.form_data = {"name": "", "id": "", "fleet": "A321", "rank": "FF"}

# --- 核心功能：對齊 CSV 欄位 (班號,起飛,目的地,起飛時間,落地時間,報到時間,報離時間) ---
def get_flight_details(flight_input):
    try:
        # 提取數字 (例如 BR116 -> 116)
        match = re.search(r'\d+', str(flight_input))
        if not match: return "非航班任務"
        
        f_no = str(match.group())
        return_f_no = int(f_no) + 1
        
        # 讀取 CSV
        df = pd.read_csv('flights.csv', encoding='utf-8-sig') 
        df['班號'] = df['班號'].astype(str).str.strip()
        detail = df[df['班號'] == f_no]
        
        if not detail.empty:
            d = detail.iloc[0]
            return (f"報到: {d['報到時間']} | "
                    f"航程: {d['起飛']} ✈️ {d['目的地']} | "
                    f"時間: {d['起飛時間']} - {d['落地時間']} | "
                    f"回程: {return_f_no} 號")
        else:
            return f"CSV 找不到班號 {f_no}"
    except Exception as e:
        return "資料比對中..."

# --- CSS 終極優化：全介面換裝「霧霾藍」、放大字體、消滅醜底色 ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 1rem !important; }
    
    /* 1. 徹底覆蓋：把 7 號（今日）的醜顏色強行改成氣質「霧霾藍」半透明 */
    .fc-day-today, 
    .fc-daygrid-day.fc-day-today,
    .fc .fc-daygrid-day.fc-day-today {
        background-color: rgba(108, 122, 137, 0.2) !important; 
        border: 1px solid #6c7a89 !important; 
    }

    /* 2. 班號大字 2.2rem */
    .fc-event-title { 
        font-size: 2.2rem !important; 
        font-weight: 900 !important; 
        color: #ffffff !important;
        text-align: center !important;
    }
    
    /* 3. 事件格子：霧霾藍側邊線 */
    .fc-v-event, .fc-daygrid-event {
        background: #111 !important;
        border-left: 4px solid #6c7a89 !important; 
        border-radius: 4px !important;
        min-height: 60px !important;
        cursor: pointer !important;
    }
    
    /* 4. 日期數字：加大至 1.4rem 亮白 */
    .fc-daygrid-day-number { 
        font-size: 1.4rem !important; 
        font-weight: 900 !important; 
        color: #ffffff !important; 
        padding: 8px !important;
    }

    /* 5. 輸入框：霧霾藍極細線 */
    input[type="text"], .stSelectbox div[data-baseweb="select"] {
        border: 1px solid #6c7a89 !important; 
        border-radius: 4px !important;
        font-size: 1rem !important;
    }
    
    .fc-theme-standard td, .fc-theme-standard th { border-color: #333 !important; }
    .fc-toolbar-title { display: none !important; }
    </style>
""", unsafe_allow_html=True)

# 4. 建立網頁排版
col_left, col_right = st.columns([0.8, 3])

with col_left:
    # 左側標題同步放大並使用霧霾藍色調
    st.markdown("<p style='font-size:1.3rem; font-weight:bold; color:#a2b5cd; margin-bottom:15px;'>班表自動辨識</p>", unsafe_allow_html=True)
    u_name = st.text_input("姓名", value=st.session_state.form_data["name"], placeholder="請輸入姓名")
    u_id = st.text_input("員編", value=st.session_state.form_data["id"], placeholder="請輸入員編")
    c1, c2 = st.columns(2)
    with c1:
        u_fleet = st.selectbox("機隊", ["A321", "B738"])
    with c2:
        u_rank = st.selectbox("職級", ["FF", "FY"])

    if st.button("儲存並同步"):
        st.session_state.form_data = {"name": u_name, "id": u_id, "fleet": u_fleet, "rank": u_rank}
        st.rerun()

    st.markdown("---")
    uploaded_file = st.file_uploader("1. 上傳班表照片", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        img = Image.open(uploaded_file)
        if st.button("🚀 開始辨識"):
            with st.spinner("AI 辨識中..."):
                success = False
                for model_name in ['gemini-2.5-flash', 'models/gemini-1.5-flash', 'gemini-1.5-flash']:
                    try:
                        model = genai.GenerativeModel(model_name=model_name)
                        prompt = "Read schedule, return JSON: [{'title': '116', 'start': '2026-04-03'}]. Year 2026."
                        response = model.generate_content([prompt, img])
                        res_text = response.text.replace('```json', '').replace('```', '').strip()
                        raw_events = json.loads(res_text)
                        
                        final_events = []
                        for ev in raw_events:
                            if "-04-" in ev['start']:
                                ev['description'] = get_flight_details(ev['title'])
                                final_events.append(ev)
                        st.session_state.calendar_events = final_events
                        success = True
                        break
                    except: continue
                if success: st.rerun()
                else: st.error("辨識失敗")

with col_right:
    form_data = st.session_state.form_data
    # --- 標題與資訊內容字體完全等大 (1.3rem) ---
    st.markdown(f"""
        <div style="border-bottom: 2px solid #6c7a89; padding-bottom: 10px; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center;">
            <div style="font-size: 1.3rem; font-weight: bold; color: white;">2026 年 4 月</div>
            <div style="display: flex; gap: 20px; font-size: 1.3rem; font-weight: bold; color: white;">
                <span>姓名: {form_data["name"] if form_data["name"] else "---"}</span>
                <span>員編: {form_data["id"] if form_data["id"] else "---"}</span>
                <span style="color: #a2b5cd;">機隊: {form_data["fleet"]}</span>
                <span style="color: #a2b5cd;">職級: {form_data["rank"]}</span>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # 渲染月曆
    cal_res = calendar(events=st.session_state.calendar_events, options={
        "initialView": "dayGridMonth", "initialDate": "2026-04-01", 
        "fixedWeekCount": False, "aspectRatio": 2.1,
        "headerToolbar": {"left":"", "center":"", "right":""}
    }, key="flight_calendar")

    # 點擊顯示詳細資訊邏輯
    if cal_res.get("callback") == "eventClick":
        event_data = cal_res.get("eventClick").get("event")
        st.toast(f"航班 {event_data.get('title')}：{event_data.get('extendedProps').get('description')}", icon="✅")