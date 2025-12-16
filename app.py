import streamlit as st
import datetime as dt
import math
import struct

# =========================
# Page setup
# =========================
st.set_page_config(page_title="MedTimer", page_icon="💊", layout="wide")

# =========================
# Session state initialization
# =========================
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

# =========================
# Color palette and helpers
# =========================
COLOR_PALETTE = ["green", "blue", "orange", "purple", "pink", "teal", "brown"]

def get_medicine_color(name: str) -> str:
    """Assign a consistent color to each medicine."""
    name = name.strip()
    if name not in st.session_state.medicine_colors:
        idx = len(st.session_state.medicine_colors) % len(COLOR_PALETTE)
        st.session_state.medicine_colors[name] = COLOR_PALETTE[idx]
    return st.session_state.medicine_colors[name]

def show_status(message: str, color: str) -> None:
    """Display a status message with a color-coded style or emoji badge."""
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

# =========================
# Utility functions
# =========================
def unique_key(date_obj: dt.date, name: str, time_obj: dt.time) -> str:
    """Create a unique key for a dose event."""
    return f"{date_obj}|{name.strip()}|{time_obj.strftime('%H:%M')}"

def mark_taken(date_obj: dt.date, name: str, time_obj: dt.time, value: bool) -> None:
    """Add or remove event from taken records and rerun."""
    key = unique_key(date_obj, name, time_obj)
    if value:
        st.session_state.taken_events.add(key)
        st.toast(f"Marked taken: {name} at {time_obj.strftime('%I:%M %p')}")
    else:
        st.session_state.taken_events.discard(key)
        st.toast(f"Unmarked: {name} at {time_obj.strftime('%I:%M %p')}")
    st.rerun()

def beep() -> None:
    """Play a short beep for due doses (silent fallback if audio fails)."""
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

def get_today_events():
    """Return today's events based on schedules and today's weekday."""
    today = dt.date.today()
    weekday = today.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        # Match full weekday or its 3-letter alias
        if any(day in s["days"] for day in [weekday, weekday[:3]]):
            for t in s["times"]:
                events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: (x["name"].lower(), x["time"]))

def get_events_for_day(day: dt.date):
    """Return events for the given day based on schedules."""
    wd = day.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        if any(w in s["days"] for w in [wd, wd[:3]]):
            for t in s["times"]:
                events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: (x["name"].lower(), x["time"]))

def status_for_event(event_time: dt.datetime, now: dt.datetime, reminder_min: int):
    """Compute status (missed/due/upcoming) and minutes until event."""
    mins_until = (event_time - now).total_seconds() / 60
    if mins_until <= 0:
        return "missed", mins_until
    elif mins_until <= reminder_min:
        return "due", mins_until
    else:
        return "upcoming", mins_until

# =========================
# Sidebar (reliable controls)
# =========================
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_min = st.slider("Reminder (minutes before)", 1, 60, st.session_state.reminder_min)

    if st.button("Reset all records"):
        st.session_state.taken_events = set()
        st.toast("All records have been reset.")
        st.rerun()

    # Optional: clear schedules if ever needed (commented by default)
    # if st.button("Clear all schedules"):
    #     st.session_state.schedules = []
    #     st.session_state.taken_events = set()
    #     st.toast("All schedules and records cleared.")
    #     st.rerun()

# =========================
# Header and layout
# =========================
st.title("Pill MedTimer")
st.caption("Never miss a dose again.")
col1, col2, col3 = st.columns([1.7, 2, 1.3])

# =========================
# Add medicine (left column)
# =========================
with col1:
    st.subheader("Add new medicine")

    name = st.text_input("Medicine name", placeholder="e.g., Paracetamol")
    days = st.multiselect(
        "Repeat on days",
        ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
        default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    )

    st.write("Dose times")
    # Dynamic time inputs with remove buttons
    i = 0
    while i < len(st.session_state.temp_doses):
        col_a, col_b = st.columns([3, 1])
        with col_a:
            new_time = st.time_input(f"Dose {i+1}", value=st.session_state.temp_doses[i], key=f"time_{i}")
            st.session_state.temp_doses[i] = new_time
        with col_b:
            if st.button("Remove", key=f"remove_{i}"):
                st.session_state.temp_doses.pop(i)
                st.rerun()
        i += 1

    if st.button("Add another dose time"):
        # Add a sensible default next time (e.g., 18:00)
        st.session_state.temp_doses.append(dt.time(18, 0))
        st.rerun()

    if st.button("Save medicine schedule", type="primary"):
        if name.strip() and len(st.session_state.temp_doses) > 0 and len(days) > 0:
            record = {
                "name": name.strip(),
                "days": days,
                "times": st.session_state.temp_doses.copy(),
                "start_date": dt.date.today()
            }
            st.session_state.schedules.append(record)
            # Assign color immediately to ensure consistent color coding
            _ = get_medicine_color(name.strip())
            st.success(f"Added: {name} ({len(st.session_state.temp_doses)} dose(s))")
            # Reset to a single default dose time for convenience
            st.session_state.temp_doses = [dt.time(8, 0)]
            st.rerun()
        else:
            st.error("Please enter a name, select days, and add at least one time.")

# =========================
# Today's checklist (middle column)
# =========================
with col2:
    st.subheader(f"Today – {dt.date.today():%A, %b %d}")
    events_today = get_today_events()
    now = dt.datetime.now()

    if not events_today:
        st.info("No medications scheduled for today.")
    else:
        for idx, e in enumerate(events_today):
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
                mins = int(max(0, mins_until))
                show_status(
                    f"Upcoming in {mins}m" if mins < 60 else f"Upcoming in {mins//60}h {mins%60}m",
                    med_color
                )

            if checked != taken:
                mark_taken(dt.date.today(), e["name"], e["time"], checked)

# =========================
# Weekly checklist (middle column)
# =========================
with col2:
    st.subheader("Weekly checklist (today + next 6 days)")
    today = dt.date.today()

    for i in range(7):
        day = today + dt.timedelta(days=i)
        st.write(f"**{day.strftime('%A')}, {day:%b %d}**")

        day_events = get_events_for_day(day)

        if not day_events:
            st.caption("No doses scheduled.")
        else:
            for jdx, e in enumerate(day_events):
                key = unique_key(day, e["name"], e["time"])
                taken = key in st.session_state.taken_events
                med_color = get_medicine_color(e["name"])

                checked = st.checkbox(
                    label=f"{e['name']} — {e['time'].strftime('%I:%M %p')}",
                    value=taken,
                    key=f"chk_week_{day}_{jdx}_{key}"
                )

                # Weekly checklist only shows Scheduled or Taken (no due/missed semantics here)
                if taken:
                    show_status("Taken", med_color)
                else:
                    show_status("Scheduled", med_color)

                if checked != taken:
                    mark_taken(day, e["name"], e["time"], checked)

# =========================
# Weekly stats / adherence (right column)
# =========================
with col3:
    st.subheader("7-day adherence (today + next 6 days)")
    expected = 0
    taken_count = 0
    today = dt.date.today()

    # Compute adherence over today + next 6 days
    for i in range(7):
        day = today + dt.timedelta(days=i)
        wd = day.strftime("%A")
        prefix = f"{day}|"

        # Count expected doses for the day
        for s in st.session_state.schedules:
            if any(w in s["days"] for w in [wd, wd[:3]]):
                expected += len(s["times"])

        # Count taken events for the day
        for tk in st.session_state.taken_events:
            if tk.startswith(prefix):
                taken_count += 1

    adherence = int(100 * taken_count / expected) if expected > 0 else 100
    st.metric("Adherence", f"{adherence}%")
    st.progress(min(adherence, 100) / 100.0)

    if adherence >= 95:
        st.success("Excellent adherence!")
    elif adherence >= 80:
        st.success("Great job!")
    elif adherence >= 60:
        st.warning("Keep going")
    else:
        st.error("Let's get back on track!")

    st.write("😊 You're doing amazing!")
