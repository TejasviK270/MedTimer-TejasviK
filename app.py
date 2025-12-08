import streamlit as st
import datetime as dt
import random
import math
import struct

# === Page Setup ===
st.set_page_config(page_title="MedTimer", page_icon="Pill", layout="wide")

# Beautiful styling
st.markdown("""
<style>
    .big-title {font-size: 3rem !important; color: #00695c; text-align: center; margin: 20px 0;}
    .pill {padding: 10px 20px; border-radius: 50px; font-weight: bold; color: white; display: inline-block;}
    .pill-green {background: #2e7d32;}
    .pill-yellow {background: #f9a825; color: black;}
    .pill-red {background: #c62828;}
    .dose-card {background: #e8f5e9; padding: 18px; border-radius: 15px; margin: 12px 0; border-left: 6px solid #4caf50;}
</style>
""", unsafe_allow_html=True)

# === Session State ===
if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "taken_events" not in st.session_state:
    st.session_state.taken_events = set()
if "reminder_min" not in st.session_state:
    st.session_state.reminder_min = 15
if "temp_doses" not in st.session_state:
    st.session_state.temp_doses = [dt.time(8, 0)]  # Start with 1 dose

# === Helper Functions ===
def unique_key(date, name, time_obj):
    return f"{date}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(date, name, time_obj):
    key = unique_key(date, name, time_obj)
    st.session_state.taken_events.add(key)
    st.success(f"Taken: {name} at {time_obj.strftime('%I:%M %p')}")
    st.rerun()

def beep():
    try:
        sr, freq, dur = 44100, 880, 0.35
        samples = int(sr * dur)
        data = bytearray()
        for i in range(samples):
            val = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sr))
            data += struct.pack("<h", val)
        header = (
            b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt " +
            struct.pack("<IHHIIHH", 16, 1, 1, sr, sr*2, 2, 16) +
            b"data" + struct.pack("<I", len(data))
        )
        st.audio(header + data, format="audio/wav", autoplay=True)
    except:
        pass

def get_today_events():
    today = dt.date.today()
    weekday = today.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        if today >= s.get("start_date", today):
            if any(day in s["days"] for day in [weekday, weekday[:3]]):
                for t in s["times"]:
                    events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: x["time"])

# === Sidebar ===
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_min = st.slider("Reminder (minutes before)", 1, 60, st.session_state.reminder_min)
    if st.button("Clear All Taken Records"):
        st.session_state.taken_events = set()
        st.rerun()

# === Header ===
st.markdown("<h1 class='big-title'>Pill MedTimer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Never miss a dose again!</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.7, 2, 1.2])

# === Add Medicine ===
with col1:
    st.subheader("Add New Medicine")

    name = st.text_input("Medicine Name", placeholder="e.g., Metformin 500mg")

    days = st.multiselect("Repeat on days",
        ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])

    st.write("**Dose Times**")
    for i in range(len(st.session_state.temp_doses)):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            new_time = st.time_input(f"Dose {i+1}", value=st.session_state.temp_doses[i], key=f"time_{i}")
            st.session_state.temp_doses[i] = new_time
        with col_b:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.temp_doses.pop(i)
                st.rerun()

    if st.button("Add Another Dose Time"):
        st.session_state.temp_doses.append(dt.time(18, 0))
        st.rerun()

    if st.button("Save Medicine Schedule", type="primary"):
        if name.strip() and st.session_state.temp_doses:
            st.session_state.schedules.append({
                "name": name.strip(),
                "days": days,
                "times": st.session_state.temp_doses.copy(),
                "start_date": dt.date.today()
            })
            st.success(f"Added: {name} ({len(st.session_state.temp_doses)} dose(s))")
            st.session_state.temp_doses = [dt.time(8, 0)]  # Reset to 1 dose
            st.rerun()
        else:
            st.error("Please enter name and at least one time")

# === Today's Doses ===
with col2:
    st.subheader(f"Today – {dt.date.today():%A, %b %d}")
    events = get_today_events()
    now = dt.datetime.now()

    if not events:
        st.info("No medications scheduled for today.")
    else:
        for idx, e in enumerate(events):
            event_dt = dt.datetime.combine(dt.date.today(), e["time"])
            mins_until = (event_dt - now).total_seconds() / 60
            key = unique_key(dt.date.today(), e["name"], e["time"])
            taken = key in st.session_state.taken_events

            st.markdown("<div class='dose-card'>", unsafe_allow_html=True)
            a, b, c = st.columns([2.8, 2, 1.8])

            with a:
                st.write(f"**{e['time'].strftime('%I:%M %p')}**")
                st.write(f"**{e['name']}**")

            with b:
                if taken:
                    st.markdown("<span class='pill pill-green'>Taken</span>", unsafe_allow_html=True)
                elif mins_until <= 0:
                    st.markdown("<span class='pill pill-red'>Missed</span>", unsafe_allow_html=True)
                elif mins_until <= st.session_state.reminder_min:
                    beep()
                    st.markdown("<span class='pill pill-yellow'>TAKE NOW</span>", unsafe_allow_html=True)
                else:
                    mins = int(mins_until)
                    st.caption(f"In {mins}m" if mins < 60 else f"In {mins//60}h {mins%60}m")

            with c:
                if taken:
                    st.write("Taken")
                else:
                    btn_key = f"taken_btn_{idx}_{e['name'].replace(' ', '_')}_{e['time'].strftime('%H%M')}"
                    if st.button("Mark Taken", key=btn_key, type="primary"):
                        mark_taken(dt.date.today(), e["name"], e["time"])

            st.markdown("</div>", unsafe_allow_html=True)

# === Weekly Stats ===
with col3:
    st.subheader("7-Day Adherence")
    expected = taken = 0
    today = dt.date.today()

    for i in range(7):
        day = today - dt.timedelta(days=i)
        wd = day.strftime("%A")
        prefix = f"{day}|"

        for s in st.session_state.schedules:
            if day >= s.get("start_date", day) and any(w in s["days"] for w in [wd, wd[:3]]):
                expected += len(s["times"])

        for tk in st.session_state.taken_events:
            if tk.startswith(prefix):
                taken += 1

    adherence = int(100 * taken / expected) if expected > 0 else 100

    st.metric("Adherence", f"{adherence}%")
    if adherence >= 95:
        st.balloons()
    elif adherence >= 80:
        st.success("Great job!")
    elif adherence >= 60:
        st.warning("Keep going")
    else:
        st.error("Let's get back on track!")

    st.caption(random.choice([
        "Every dose counts!",
        "You're doing amazing!",
        "Consistency is key!",
        "Health first!"
    ]))

    if st.button("Reset All Records"):
        st.session_state.taken_events = set()
        st.rerun()
