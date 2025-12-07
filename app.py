# app.py
import streamlit as st
import datetime as dt
import random
import math
import struct

st.set_page_config(page_title="MedTimer", page_icon="Pill", layout="wide")

st.markdown("""
<style>
    body {background:#F0F8FF; color:#004d40; font-size:18px;}
    h1,h2,h3 {color:#00695C;}
    .pill {padding:4px 12px; border-radius:999px; font-weight:600; color:white; margin-left:8px;}
    .pill-green {background:#2E7D32;}
    .pill-yellow {background:#FBC02D; color:#000;}
</style>
""", unsafe_allow_html=True)

# Session state
if "schedules" not in st.session_state: st.session_state.schedules = []
if "taken_events" not in st.session_state: st.session_state.taken_events = set()
if "reminder_minutes" not in st.session_state: st.session_state.reminder_minutes = 15

COMMON_MEDICINES = ["Aspirin","Ibuprofen","Paracetamol","Metformin","Vitamin D","Custom"]
DAY_ORDER = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
QUOTES = ["Every dose counts!","Keep going!","You're doing great!","Health first!"]

def weekday_name(d): return DAY_ORDER[d.weekday()]
def key(date, name, time): return f"{date}|{name}|{time.strftime('%H:%M')}"

def mark_taken(date, name, time):
    st.session_state.taken_events.add(key(date, name, time))
    st.rerun()

def beep():
    samples = int(0.3 * 44100)
    data = bytearray()
    for i in range(samples):
        v = int(32767 * 0.4 * math.sin(2 * math.pi * 880 * i / 44100))
        data += struct.pack("<h", v)
    wav = b"RIFF" + struct.pack("<I",36+len(data)) + b"WAVEfmt " + struct.pack("<IHHIIHH",16,1,1,44100,88200,2,16) + b"data" + struct.pack("<I",len(data)) + data
    st.audio(wav, format="audio/wav", autoplay=True)

def todays_events():
    today = dt.date.today()
    events = []
    for s in st.session_state.schedules:
        if today >= s["start_date"] and weekday_name(today) in s["days_of_week"]:
            for t in s["times"]:
                events.append({"name":s["name"], "time":t})
    return sorted(events, key=lambda x: x["time"])

def weekly_adherence():
    today = dt.date.today()
    monday = today - dt.timedelta(days=today.weekday())
    total = taken = 0
    for i in range(7):
        d = monday + dt.timedelta(days=i)
        for s in st.session_state.schedules:
            if d >= s["start_date"] and weekday_name(d) in s["days_of_week"]:
                for t in s["times"]:
                    total += 1
                    if key(d, s["name"], t) in st.session_state.taken_events:
                        taken += 1
    return int(taken/total*100) if total else 100

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_minutes = st.slider("Reminder before (min)",1,60,st.session_state.reminder_minutes)

# Main layout
st.title("Pill MedTimer")
c1, c2, c3 = st.columns([1.4, 1.8, 1.2])

with c1:
    st.subheader("Add medicine")
    choice = st.selectbox("Pick or type", ["Custom"]+COMMON_MEDICINES)
    name = st.text_input("Name", "" if choice=="Custom" else choice)
    days = st.multiselect("Days", DAY_ORDER, default=[weekday_name(dt.date.today())])
    n = st.number_input("Doses/day",1,6,1)
    times = [st.time_input(f"Time {i+1}", dt.time(9+i*3), key=f"t{i}") for i in range(n)]
    start = st.date_input("Start", dt.date.today())

    if st.button("Add"):
        if name.strip() and days:
            st.session_state.schedules.append({"name":name.strip(),"days_of_week":days,"times":times,"start_date":start})
            st.success("Added!")
            st.rerun()
        else:
            st.warning("Fill name & days")

with c2:
    st.subheader("Today")
    now = dt.datetime.now()
    events = todays_events()
    if not events:
        st.info("No doses today")
    else:
        for e in events:
            k = key(dt.date.today(), e["name"], e["time"])
            taken = k in st.session_state.taken_events
            mins = (dt.datetime.combine(dt.date.today(), e["time"]) - now).total_seconds()/60

            a,b,c = st.columns([4,1,1])
            with a:
                st.write(f"**{e['time'].strftime('%H:%M')}** – {e['name']}  {'Taken' if taken else 'Upcoming'}")
            with b:
                if 0 < mins <= st.session_state.reminder_minutes:
                    beep()
                    st.markdown("<span class='pill pill-yellow'>NOW</span>", unsafe_allow_html=True)
                elif taken:
                    st.markdown("<span class='pill pill-green'>DONE</span>", unsafe_allow_html=True)
            with c:
                if not taken and st.button("Taken", key=k):
                    mark_taken(dt.date.today(), e["name"], e["time"])

with c3:
    st.subheader("Week")
    adh = weekly_adherence()
    st.metric("Adherence", f"{adh}%")
    if adh >= 95:
        st.success("Perfect week! Trophy")
        st.balloons()
    st.caption(random.choice(QUOTES))
    if st.button("Reset week"):
        st.session_state.taken_events = set()
        st.rerun()
