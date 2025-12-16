import streamlit as st
import datetime as dt
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

def get_medicine_color(name: str) -> str:
    if name not in st.session_state.medicine_colors:
        idx = len(st.session_state.medicine_colors) % len(COLOR_PALETTE)
        st.session_state.medicine_colors[name] = COLOR_PALETTE[idx]
    return st.session_state.medicine_colors[name]

def show_status(message: str, color: str) -> None:
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

# === Utility Functions ===
def unique_key(date_obj: dt.date, name: str, time_obj: dt.time) -> str:
    return f"{date_obj}|{name.strip()}|{time_obj.strftime('%H:%M')}"

def mark_taken(date_obj: dt.date, name: str, time_obj: dt.time, value: bool) -> None:
    key = unique_key(date_obj, name, time_obj)
    if value:
        st.session_state.taken_events.add(key)
    else:
        st.session_state.taken_events.discard(key)
    # No rerun here — caller will handle it to avoid multiple reruns

def is_taken(date_obj: dt.date, name: str, time_obj: dt.time) -> bool:
    key = unique_key(date_obj, name, time_obj)
    return key in st.session_state.taken_events

def beep() -> None:
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
    except Exception:
        pass

def get_events_for_day(day: dt.date):
    wd = day.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        if any(w in s["days"] for w in [wd, wd[:3]]):
            for t in s["times"]:
                events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: (x["name"].lower(), x["time"]))

def status_for_event(event_time: dt.datetime, now: dt.datetime, reminder_min: int):
    mins_until = (event_time - now).total_seconds() / 60
    if mins_until <= 0:
        return "missed", mins_until
    elif mins_until <= reminder_min:
        return "due", mins_until
    else:
        return "upcoming", mins_until

def calculate_adherence_score() -> tuple[int, int, int]:
    """Returns (taken, total, percentage) over last 7 days"""
    today = dt.date.today()
    taken_count = 0
    total_count = 0
    for i in range(7):
        day = today - dt.timedelta(days=i)  # past 7 days including today
        events = get_events_for_day(day)
        for e in events:
            total_count += 1
            if is_taken(day, e["name"], e["time"]):
                taken_count += 1
    percentage = (taken_count / total_count * 100) if total_count > 0 else 100
    return taken_count, total_count, round(percentage)

# === Sidebar ===
with st.sidebar:
    st.header("🛠 Settings")
    st.session_state.reminder_min = st.slider(
        "Reminder (minutes before)", 1, 60, st.session_state.reminder_min
    )
    st.divider()
    if st.button("🔄 Reset All Taken Records", type="secondary"):
        st.session_state.taken_events = set()
        st.toast("All taken records have been reset!", icon="🗑️")
        st.rerun()
    st.divider()
    st.caption("MedTimer 🐢 v1.0")

# === Header ===
st.title("🐢 Pill MedTimer")
st.caption("Never miss a dose again – stay consistent!")

# Adherence Score (Prominent)
taken, total, score = calculate_adherence_score()
if total == 0:
    st.info("No doses scheduled in the last 7 days yet.")
else:
    st.metric(label="📊 7-Day Adherence Score", value=f"{score}%")
    if score == 100:
        st.success("🐢 Perfect adherence! Amazing consistency! 🎉")
    elif score >= 80:
        st.success("🐢 Great job! Keep it up! 💪")
    elif score >= 60:
        st.warning("🐢 Doing okay – let's improve a bit! 🌱")
    else:
        st.error("🐢 Room for improvement – you got this! 💊")

col1, col2, col3 = st.columns([1.7, 2, 1.3])

# === Add Medicine ===
with col1:
    st.subheader("➕ Add New Medicine")
    name = st.text_input("Medicine name", placeholder="e.g., Vitamin D")
    days = st.multiselect(
        "Repeat on days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    )
    st.write("**Dose times**")
    for i in range(len(st.session_state.temp_doses)):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            new_time = st.time_input(
                f"Dose {i+1}", value=st.session_state.temp_doses[i], key=f"time_{i}"
            )
            st.session_state.temp_doses[i] = new_time
        with col_b:
            if st.button("❌", key=f"remove_{i}"):
                st.session_state.temp_doses.pop(i)
                st.rerun()
    if st.button("➕ Add another dose time"):
        st.session_state.temp_doses.append(dt.time(18, 0))
        st.rerun()

    if st.button("💾 Save Medicine Schedule", type="primary"):
        if name.strip() and days and st.session_state.temp_doses:
            st.session_state.schedules.append({
                "name": name.strip(),
                "days": days,
                "times": st.session_state.temp_doses.copy(),
                "start_date": dt.date.today()
            })
            _ = get_medicine_color(name.strip())
            st.success(f"Added: **{name.strip()}** ({len(st.session_state.temp_doses)} dose(s))")
            st.session_state.temp_doses = [dt.time(8, 0)]
            st.rerun()
        else:
            st.error("Please fill in name, days, and at least one time.")

# === Today's Checklist ===
with col2:
    st.subheader(f"📅 Today – {dt.date.today():%A, %b %d}")
    events_today = get_events_for_day(dt.date.today())
    now = dt.datetime.now()

    if not events_today:
        st.info("No medications scheduled for today.")
    else:
        for idx, e in enumerate(events_today):
            event_dt = dt.datetime.combine(dt.date.today(), e["time"])
            status, mins_until = status_for_event(event_dt, now, st.session_state.reminder_min)
            key = unique_key(dt.date.today(), e["name"], e["time"])
            taken = is_taken(dt.date.today(), e["name"], e["time"])
            med_color = get_medicine_color(e["name"])

            checked = st.checkbox(
                label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                value=taken,
                key=f"today_chk_{idx}_{key}"
            )

            # Status message
            if taken:
                show_status("✅ Taken", med_color)
            elif status == "missed":
                show_status("❌ Missed", "red")
            elif status == "due":
                beep()
                show_status("🔔 Due now!", "orange")
            else:
                mins = int(max(0, mins_until))
                time_str = f"{mins}m" if mins < 60 else f"{mins//60}h {mins%60}m"
                show_status(f"⏳ Upcoming in {time_str}", med_color)

            # Sync if changed
            if checked != taken:
                mark_taken(dt.date.today(), e["name"], e["time"], checked)
                st.rerun()  # Sync immediately

# === Weekly Checklist ===
with col3:
    st.subheader("📆 Weekly View (Today + Next 6 Days)")
    today = dt.date.today()
    for i in range(7):
        day = today + dt.timedelta(days=i)
        day_str = "Today" if i == 0 else day.strftime("%A")
        st.write(f"**{day_str}, {day:%b %d}**")

        day_events = get_events_for_day(day)
        if not day_events:
            st.caption("_(no doses)_")
            continue

        for jdx, e in enumerate(day_events):
            key = unique_key(day, e["name"], e["time"])
            taken = is_taken(day, e["name"], e["time"])
            med_color = get_medicine_color(e["name"])

            checked = st.checkbox(
                label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                value=taken,
                key=f"week_chk_{i}_{jdx}_{key}"
            )

            if checked != taken:
                mark_taken(day, e["name"], e["time"], checked)
                st.rerun()  # Immediate sync

st.markdown("---")
st.caption("Made with 🐢 care | Stay healthy and consistent!")
