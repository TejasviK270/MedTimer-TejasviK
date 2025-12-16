import streamlit as st
import datetime as dt
import random
import math
import struct

# === Page Setup ===
st.set_page_config(page_title="MedTimer", page_icon="💊", layout="wide")

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

def mark_taken(date, name, time_obj, value: bool):
    key = unique_key(date, name, time_obj)
    if value:
        st.session_state.taken_events.add(key)
        st.toast(f"Marked taken: {name} at {time_obj.strftime('%I:%M %p')}")
    else:
        st.session_state.taken_events.discard(key)
        st.toast(f"Unmarked: {name} at {time_obj.strftime('%I:%M %p')}")
    st.rerun()

def beep():
    try:
        sr, freq, dur = 44100, 880, 0.25
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

def status_for_event(event_time, now, reminder_min):
    mins_until = (event_time - now).total_seconds() / 60
    if mins_until <= 0:
        return "missed", mins_until
    elif mins_until <= reminder_min:
        return "due", mins_until
    else:
        return "upcoming", mins_until

# === Sidebar ===
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_min = st.slider("Reminder (minutes before)", 1, 60, st.session_state.reminder_min)
    if st.button("Clear All Taken Records"):
        st.session_state.taken_events = set()
        st.rerun()

# === Header ===
st.title("Pill MedTimer")
st.caption("Never miss a dose again.")

col1, col2, col3 = st.columns([1.7, 2, 1.3])

# === Add Medicine ===
with col1:
    st.subheader("Add new medicine")

    name = st.text_input("Medicine name", placeholder="e.g., Metformin 500mg")

    days = st.multiselect(
        "Repeat on days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    )

    st.write("Dose times")
    for i in range(len(st.session_state.temp_doses)):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            new_time = st.time_input(f"Dose {i+1}", value=st.session_state.temp_doses[i], key=f"time_{i}")
            st.session_state.temp_doses[i] = new_time
        with col_b:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.temp_doses.pop(i)
                st.rerun()

    if st.button("Add another dose time"):
        st.session_state.temp_doses.append(dt.time(18, 0))
        st.rerun()

    if st.button("Save medicine schedule", type="primary"):
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
            st.error("Please enter a name and at least one time")

# === Today's Doses: Color-coded checklist ===
with col2:
    st.subheader(f"Today – {dt.date.today():%A, %b %d}")
    events = get_today_events()
    now = dt.datetime.now()

    if not events:
        st.info("No medications scheduled for today.")
    else:
        for idx, e in enumerate(events):
            event_dt = dt.datetime.combine(dt.date.today(), e["time"])
            status, mins_until = status_for_event(event_dt, now, st.session_state.reminder_min)
            key = unique_key(dt.date.today(), e["name"], e["time"])
            taken = key in st.session_state.taken_events

            # Checklist row
            left, mid, right = st.columns([2.6, 2.2, 2.2])
            with left:
                checked = st.checkbox(
                    label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                    value=taken,
                    key=f"chk_{idx}_{key}"
                )
            with mid:
                if status == "missed":
                    st.error("Missed")
                elif status == "due":
                    st.warning("Due now")
                    beep()
                else:
                    mins = int(mins_until)
                    st.info(f"In {mins}m" if mins < 60 else f"In {mins//60}h {mins%60}m")
            with right:
                if checked != taken:
                    if checked:
                        mark_taken(dt.date.today(), e["name"], e["time"], True)
                    else:
                        mark_taken(dt.date.today(), e["name"], e["time"], False)

# === Weekly Stats: Adherence score + turtle smiley ===
with col3:
    st.subheader("7-day adherence")
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

    # Visual progress (no emojis, no balloons)
    if expected > 0:
        st.progress(min(adherence, 100) / 100.0)
    else:
        st.info("No scheduled doses in the last 7 days.")

    # Encouragement without emojis
    if adherence >= 95:
        st.success("Excellent adherence!")
    elif adherence >= 80:
        st.success("Great job!")
    elif adherence >= 60:
        st.warning("Keep going")
    else:
        st.error("Let's get back on track!")

  # ACC-style smiley emoji
st.write("😊 You're doing amazing!")

st.caption(random.choice([
        "Every dose counts.",
        "Consistency is key.",
        "Small steps, big results.",
        "Health first."
    ]))

if st.button("Reset all records"):
        st.session_state.taken_events = set()
        st.rerun()
