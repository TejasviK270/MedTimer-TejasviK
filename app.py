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
    st.session_state.temp_doses = [dt.time(8, 0)]
if "medicine_colors" not in st.session_state:
    st.session_state.medicine_colors = {}

# === Color Palette ===
COLOR_PALETTE = ["green", "blue", "orange", "purple", "pink", "teal", "brown"]

def get_medicine_color(name):
    if name not in st.session_state.medicine_colors:
        idx = len(st.session_state.medicine_colors) % len(COLOR_PALETTE)
        st.session_state.medicine_colors[name] = COLOR_PALETTE[idx]
    return st.session_state.medicine_colors[name]

def show_status(message, color):
    if color == "green":
        st.success(message)
    elif color == "blue":
        st.info(message)
    elif color == "orange":
        st.warning(message)
    elif color == "red":
        st.error(message)
    elif color == "purple":
        st.write(f"🟣 {message}")
    elif color == "pink":
        st.write(f"🌸 {message}")
    elif color == "teal":
        st.write(f"🟦 {message}")
    elif color == "brown":
        st.write(f"🟤 {message}")
    else:
        st.write(message)

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
            st.session_state.temp_doses = [dt.time(8, 0)]
            st.rerun()
        else:
            st.error("Please enter a name and at least one time")

# === Today's Checklist ===
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

            med_color = get_medicine_color(e["name"])

            checked = st.checkbox(
                label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                value=taken,
                key=f"chk_today_{idx}_{key}"
            )

            if taken:
                show_status("Taken", med_color)
            elif status == "missed":
                show_status("Missed", "red")
            elif status == "due":
                beep()
                show_status("Due now", "orange")
            else:
                mins = int(mins_until)
                show_status(f"Upcoming in {mins}m" if mins < 60 else f"Upcoming in {mins//60}h {mins%60}m", med_color)

            if checked != taken:
                mark_taken(dt.date.today(), e["name"], e["time"], checked)

# === Weekly Checklist (today + next 6 days) ===
with col2:
    st.subheader("Weekly Checklist (today + next 6 days)")
    today = dt.date.today()

    for i in range(7):
        day = today + dt.timedelta(days=i)
        wd = day.strftime("%A")
        st.write(f"**{wd}, {day:%b %d}**")

        events = []
        for s in st.session_state.schedules:
            if any(w in s["days"] for w in [wd, wd[:3]]):
                for t in s["times"]:
                    events.append({"name": s["name"], "time": t})

        if not events:
            st.caption("No doses scheduled.")
        else:
            for idx, e in enumerate(events):
                key = unique_key(day, e["name"], e["time"])
                taken = key in st.session_state.taken_events
                med_color = get_medicine_color(e["name"])

                checked = st.checkbox(
                    label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                    value=taken,
                    key=f"chk_week_{day}_{idx}_{key}"
                )

                if taken:
                    show_status("Taken",
