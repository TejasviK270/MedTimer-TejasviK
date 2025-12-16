import streamlit as st
import datetime as dt
import math
import struct
import random

# === Page Setup ===
st.set_page_config(page_title="MedTimer", page_icon="💊", layout="wide")

# === Session State Initialization ===
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
if "editing_index" not in st.session_state:
    st.session_state.editing_index = None

# === Color Palette ===
COLOR_PALETTE = ["green", "blue", "orange", "purple", "pink", "teal", "brown"]

def get_medicine_color(name: str) -> str:
    if name not in st.session_state.medicine_colors:
        idx = len(st.session_state.medicine_colors) % len(COLOR_PALETTE)
        st.session_state.medicine_colors[name] = COLOR_PALETTE[idx]
    return st.session_state.medicine_colors[name]

# === Utility Functions ===
def unique_key(date_obj: dt.date, name: str, time_obj: dt.time) -> str:
    return f"{date_obj}|{name.strip()}|{time_obj.strftime('%H:%M')}"

def mark_taken(date_obj: dt.date, name: str, time_obj: dt.time, value: bool) -> None:
    key = unique_key(date_obj, name, time_obj)
    if value:
        st.session_state.taken_events.add(key)
    else:
        st.session_state.taken_events.discard(key)

def is_taken(date_obj: dt.date, name: str, time_obj: dt.time) -> bool:
    return unique_key(date_obj, name, time_obj) in st.session_state.taken_events

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

def calculate_adherence_score():
    today = dt.date.today()
    taken_count = total_count = 0
    for i in range(7):
        day = today - dt.timedelta(days=i)
        events = get_events_for_day(day)
        for e in events:
            total_count += 1
            if is_taken(day, e["name"], e["time"]):
                taken_count += 1
    percentage = (taken_count / total_count * 100) if total_count > 0 else 100
    return taken_count, total_count, round(percentage)

def get_random_tip():
    tips = [
        "Remember to stay hydrated while taking your meds!",
        "Consistency is key – small steps lead to big improvements.",
        "Set a gentle reminder tone to make tracking feel less stressful.",
        "Celebrate your wins, no matter how small!",
        "Talk to your doctor if you have questions about your schedule.",
        "A calm mind helps with remembering doses – take deep breaths.",
        "Use colors to organize your meds visually.",
        "You're doing great – keep up the good work!",
        "Pair your meds with a favorite routine, like breakfast.",
        "Empower yourself by tracking your progress daily."
    ]
    return random.choice(tips)

def draw_turtle():
    turtle_ascii = """
       .-""-.
      /      \\
     |        |
     |        |
      \\      /
       `----'
    """
    st.markdown("🐢 **Turtle Says: Great Job!**")
    st.code(turtle_ascii, language="")

# === Sidebar ===
with st.sidebar:
    st.header("🛠 Settings")
    st.session_state.reminder_min = st.slider("Reminder (minutes before)", 1, 60, st.session_state.reminder_min)
    st.divider()
    if st.button("🔄 Reset All Taken Records", type="secondary"):
        st.session_state.taken_events = set()
        st.toast("All records reset!", icon="🗑️")
        st.rerun()
    st.divider()
    st.caption("MedTimer 🐢 v1.1")

# === Header & Adherence Score ===
st.title("🐢 Pill MedTimer")
st.caption("Track your meds • Stay consistent • Feel better")

taken, total, score = calculate_adherence_score()
if total == 0:
    st.info("No scheduled doses in the last 7 days.")
else:
    col_a, col_b = st.columns([1, 3])
    with col_a:
        st.metric("📊 7-Day Adherence", f"{score}%")
        if score >= 80:
            draw_turtle()
    with col_b:
        if score == 100:
            st.success("🐢 Perfect! You're crushing it! 🎉")
        elif score >= 80:
            st.success("🐢 Excellent consistency! Keep going! 💪")
        elif score >= 60:
            st.warning("🐢 Good effort – a little more and you're there! 🌟")
        else:
            st.error("🐢 Let's get back on track – you've got this! 💊")

st.divider()

# === Motivational Tip ===
st.subheader("💡 Daily Tip")
st.info(get_random_tip())

st.divider()

col1, col2, col3 = st.columns([1.8, 2, 1.8])

# === Add/Edit/Delete Medicine ===
with col1:
    st.subheader("➕ Add/Edit Medicine")
    if st.session_state.editing_index is not None:
        sched = st.session_state.schedules[st.session_state.editing_index]
        name = st.text_input("Medicine name", value=sched["name"], placeholder="e.g., Paracetamol")
        days = st.multiselect(
            "Repeat on days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=sched["days"]
        )
        st.session_state.temp_doses = sched["times"].copy()
    else:
        name = st.text_input("Medicine name", placeholder="e.g., Paracetamol")
        days = st.multiselect(
            "Repeat on days",
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
        )
    
    st.write("**Dose times**")
    for i in range(len(st.session_state.temp_doses)):
        c1, c2 = st.columns([3, 1])
        with c1:
            new_time = st.time_input(f"Dose {i+1}", st.session_state.temp_doses[i], key=f"t{i}")
            st.session_state.temp_doses[i] = new_time
        with c2:
            if st.button("❌", key=f"rm{i}"):
                st.session_state.temp_doses.pop(i)
                st.rerun()
    if st.button("➕ Add dose time"):
        st.session_state.temp_doses.append(dt.time(18, 0))
        st.rerun()

    if st.session_state.editing_index is not None:
        if st.button("💾 Update Schedule", type="primary"):
            if name.strip() and days and st.session_state.temp_doses:
                st.session_state.schedules[st.session_state.editing_index] = {
                    "name": name.strip(),
                    "days": days,
                    "times": st.session_state.temp_doses.copy(),
                }
                get_medicine_color(name.strip())
                st.success(f"Updated **{name.strip()}**")
                st.session_state.temp_doses = [dt.time(8, 0)]
                st.session_state.editing_index = None
                st.rerun()
            else:
                st.error("Complete all fields.")
        if st.button("❌ Cancel Edit"):
            st.session_state.editing_index = None
            st.session_state.temp_doses = [dt.time(8, 0)]
            st.rerun()
    else:
        if st.button("💾 Save Schedule", type="primary"):
            if name.strip() and days and st.session_state.temp_doses:
                st.session_state.schedules.append({
                    "name": name.strip(),
                    "days": days,
                    "times": st.session_state.temp_doses.copy(),
                })
                get_medicine_color(name.strip())
                st.success(f"Added **{name.strip()}**")
                st.session_state.temp_doses = [dt.time(8, 0)]
                st.rerun()
            else:
                st.error("Complete all fields.")
    
    st.subheader("📋 Manage Medicines")
    for idx, sched in enumerate(st.session_state.schedules):
        with st.expander(f"{sched['name']} - {', '.join(sched['days'])}"):
            st.write(f"Times: {', '.join([t.strftime('%I:%M %p') for t in sched['times']])}")
            col_edit, col_delete = st.columns(2)
            with col_edit:
                if st.button("✏️ Edit", key=f"edit_{idx}"):
                    st.session_state.editing_index = idx
                    st.rerun()
            with col_delete:
                if st.button("🗑️ Delete", key=f"delete_{idx}"):
                    del st.session_state.schedules[idx]
                    st.success(f"Deleted {sched['name']}")
                    st.rerun()

# === Today's Checklist ===
with col2:
    st.subheader(f"📅 Today – {dt.date.today():%A, %b %d}")
    today_events = get_events_for_day(dt.date.today())
    now = dt.datetime.now()

    if not today_events:
        st.info("No doses scheduled today. Relax! 😊")
    else:
        for idx, event in enumerate(today_events):
            event_dt = dt.datetime.combine(dt.date.today(), event["time"])
            status, _ = status_for_event(event_dt, now, st.session_state.reminder_min)
            key = unique_key(dt.date.today(), event["name"], event["time"])
            currently_taken = is_taken(dt.date.today(), event["name"], event["time"])

            # Checkbox
            checked = st.checkbox(
                f"**{event['name']}** — {event['time'].strftime('%I:%M %p')}",
                value=currently_taken,
                key=f"today_{idx}_{key}"
            )

            # Handle change and sync
            if checked != currently_taken:
                mark_taken(dt.date.today(), event["name"], event["time"], checked)
                st.rerun()  # Immediate update across app

            # Visual feedback with color codes (no text mentions)
            if checked:
                st.success("✅ Taken", icon="💊")
            elif status == "missed":
                st.error("❌ Missed")
            elif status == "due":
                beep()  # Audio alert
                st.warning("🔔 Due now!", icon="⚠️")
            else:
                st.warning("⏳ Upcoming", icon="🕐")

# === Weekly View ===
with col3:
    st.subheader("📆 Weekly View\n(Today + Next 6 Days)")
    today = dt.date.today()

    for offset in range(7):
        day = today + dt.timedelta(days=offset)
        day_label = "Today" if offset == 0 else day.strftime("%A")
        st.markdown(f"**{day_label}, {day:%b %d}**")

        day_events = get_events_for_day(day)
        if not day_events:
            st.caption("_no doses_")
            st.markdown("---")
            continue

        for jdx, event in enumerate(day_events):
            key = unique_key(day, event["name"], event["time"])
            taken = is_taken(day, event["name"], event["time"])

            checked = st.checkbox(
                f"{event['name']} — {event['time'].strftime('%I:%M %p')}",
                value=taken,
                key=f"week_{offset}_{jdx}_{key}"
            )

            if checked != taken:
                mark_taken(day, event["name"], event["time"], checked)
                st.rerun()  # Syncs immediately – including with Today's view

        st.markdown("---")

st.caption("Made with 🐢 | Stay healthy and consistent!")
