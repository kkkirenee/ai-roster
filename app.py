Skip to content
kkkirenee
ai-roster
Repository navigation
Code
Issues
Pull requests
Actions
Projects
Wiki
Security and quality
Insights
Settings
Important update
On April 24 we'll start using GitHub Copilot interaction data for AI model training unless you opt out. Review this update and manage your preferences in your GitHub account settings.
Files
Go to file
t
app.py
my_flights.csv
requirements.txt
ai-roster
/
app.py
in
main

Edit

Preview
Indent mode

Spaces
Indent size

4
Line wrap mode

No wrap
Editing app.py file contents
  1
  2
  3
  4
  5
  6
  7
  8
  9
 10
 11
 12
 13
 14
 15
 16
 17
 18
 19
 20
 21
 22
 23
 24
 25
 26
 27
 28
 29
 30
 31
 32
 33
 34
 35
 36
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

Use Control + Shift + m to toggle the tab key moving focus. Alternatively, use esc then tab to move to the next interactive element on the page.
 
