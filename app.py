import streamlit as st
import datetime as dt
import random, math, struct

st.set_page_config(page_title="MedTimer", page_icon="Pill", layout="wide")
st.markdown("<style>body{background:#F0F8FF;color:#004d40;font-size:18px}h1,h2,h3{color:#00695C}.pill{padding:4px 12px;border-radius:999px;font-weight:600;color:white;margin-left:8px}.pill-green{background:#2E7D32}.pill-yellow{background:#FBC02D;color:#000}</style>", unsafe_allow_html=True)

# Session state
for k, v in [("schedules",[]), ("taken_events",set()), ("reminder_minutes",15)]:
    if k not in st.session_state: st.session_state[k] = v

def key(d,n,t): return f"{d}|{n}|{t.strftime('%H:%M')}"
def mark(d,n,t):
    st.session_state.taken_events.add(key(d,n,t))
    st.rerun()

def beep():
    s = 44100
    data = bytearray()
    for i in range(int(0.3*s)):
        v = int(32767*0.4*math.sin(2*math.pi*880*i/s))
        data += struct.pack("<h", v)
    wav = b"RIFF"+struct.pack("<I",36+len(data))+b"WAVEfmt "+struct.pack("<IHHIIHH",16,1,1,s,s*2,2,16)+b"data"+struct.pack("<I",len(data))+data
    st.audio(wav, format="audio/wav", autoplay=True)

def today_events():
    today = dt.date.today()
    return sorted([{"name":s["name"],"time":t} for s in st.session_state.schedules 
                   if today >= s["start_date"] and (dt.date.today().strftime("%A") in s["days_of_week"] or dt.date.today().strftime("%A")[:3] in s["days_of_week"])
                   for t in s["times"]], key=lambda x: x["time"])

with st.sidebar:
    st.session_state.reminder_minutes = st.slider("Reminder (min before)",1,60,st.session_state.reminder_minutes)

st.title("Pill MedTimer")
c1,c2,c3 = st.columns([1.4,1.8,1.2])

with c1:
    st.subheader("Add medicine")
    name = st.text_input("Medicine name")
    days = st.multiselect("Days", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"], default=["Monday"])
    n = st.number_input("Doses/day",1,6,1)
    times = [st.time_input(f"Time {i+1}", dt.time(9+i*3), key=f"t{i}") for i in range(n)]
    if st.button("Add schedule") and name and days:
        st.session_state.schedules.append({"name":name,"days_of_week":days,"times":times,"start_date":dt.date.today()})
        st.success("Added!"); st.rerun()

with c2:
    st.subheader("Today")
    now = dt.datetime.now()
    for e in today_events():
        k = key(dt.date.today(), e["name"], e["time"])
        taken = k in st.session_state.taken_events
        mins = (dt.datetime.combine(dt.date.today(), e["time"]) - now).total_seconds()/60
        a,b,c = st.columns([4,1,1])
        with a: st.write(f"**{e['time'].strftime('%H:%M')}** – {e['name']}  {'Taken' if taken else 'Pending'}")
        with b:
            if 0<mins<=st.session_state.reminder_minutes: beep(); st.markdown("<span class='pill pill-yellow'>NOW</span>", unsafe_allow_html=True)
            elif taken: st.markdown("<span class='pill pill-green'>DONE</span>", unsafe_allow_html=True)
        with c:
            if not taken and st.button("Taken",key=k): mark(dt.date.today(), e["name"], e["time"])

with c3:
    st.subheader("This week")
    total = taken = len(st.session_state.taken_events), len([1 for s in st.session_state.schedules for t in s["times"] for d in range(7) if (dt.date.today()-dt.timedelta(d)).weekday() < 7])
    adh = 100 
    if total==0:
        else int(taken/total*100)
    st.metric("Adherence", f"{adh}%")
    if adh >= 95: st.balloons()
    st.caption(random.choice(["Keep going!","Great job!","Every dose counts!"]))
    if st.button("Reset week"): st.session_state.taken_events = set(); st.rerun()
