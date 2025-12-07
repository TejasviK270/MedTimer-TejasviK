# app.py
import streamlit as st
import datetime as dt
import random
import math
import struct

# Optional: Turtle graphics (desktop only – will be skipped on Streamlit Cloud)
try:
    import turtle
    TURTLE_AVAILABLE = True
except Exception:
    TURTLE_AVAILABLE = False

# ------------------------------
# App config
# ------------------------------
st.set_page_config(page_title="MedTimer Companion", page_icon="Pill", layout="wide")

# ------------------------------
# Styling
# ------------------------------
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 18px;
        background-color: #F0F8FF;
        color: #004d40;
    }
    h1, h2, h3 {
        color: #00695C;
    }
    .pill {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 999px;
        font-weight: 600;
        color: white;
        margin-left: 8px;
    }
    .pill-green { background: #2E7D32; }
    .pill-yellow { background: #FBC02D; color: #1a1a1a; }
    .pill-red { background: #D32F2F; }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Session state initialization
# ------------------------------
if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "taken_events" not in st.session_state:
    st.session_state.taken_events = set()
if "reminder_minutes" not in st.session_state:
    pass  # keep existing value
else:
    st.session_state.reminder_minutes = 15

# ------------------------------
# Constants
# ------------------------------
COMMON_MEDICINES = sorted([
    "Aspirin", "Amoxicillin", "Azithromycin", "Atorvastatin", "Acetaminophen", "Albuterol",
    "Ibuprofen", "Insulin", "Indomethacin", "Ivermectin", "Iron Supplement",
    "Levothyroxine", "Lisinopril", "Losartan", "Metformin", "Montelukast",
    "Omeprazole", "Ondansetron", "Paracetamol", "Pantoprazole", "Prednisone",
    "Sertraline", "Simvastatin", "Tramadol", "Tamsulosin", "Vitamin D", "Warfarin"
])

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

QUOTES = [
    "Every dose taken is a step toward wellness.",
    "Consistency builds strength.",
    "You're doing great—keep it up!",
    "Health is the real wealth.",
    "Small steps lead to big changes.",
    "Your effort today shapes your tomorrow.",
    "Peace of mind starts with care.",
    "One dose at a time, you're healing.",
    "Celebrate every dose taken!",
]

# ------------------------------
# Helper functions
# ------------------------------
def weekday_name(date_obj):
    return DAY_ORDER[date_obj.weekday()]

def event_key(date_obj, name, time_obj):
    return f"{date_obj.isoformat()}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(date_obj, name, time_obj):
    st.session_state.taken_events.add(event_key(date_obj, name, time_obj))
    st.rerun()  # refresh immediately so the checkmark appears

def generate_beep():
    duration_sec = 0.3
    freq_hz = 880
    sample_rate = 44100
    volume = 0.4
    n_samples = int(duration_sec * sample_rate)

    def _le32(x): return struct.pack("<I", x)
    def _le16(x): return struct.pack("<H", x)

    byte_rate = sample_rate * 2
    block_align = 2
    data_chunk_size = n_samples * 2

    header = b"RIFF" + _le32(36 + data_chunk_size) + b"WAVE"
    fmt = b"fmt " + _le32(16) + _le16(1) + _le16(1) + _le32(sample_rate) + _le32(byte_rate) + _le16(block_align) + _le16(16)
    data_hdr = b"data" + _le32(data_chunk_size)

    data = bytearray()
    for i in range(n_samples):
        t = i / sample_rate
        sample = int(32767 * volume * math.sin(2 * math.pi * freq_hz * t))
        data += struct.pack("<h", sample)

    return header + fmt + data_hdr + data

def auto_beep():
    st.audio(generate_beep(), format="audio/wav", autoplay=True)

def occurrences_for_date(date_obj):
    wname = weekday_name(date_obj)
    occ = []
    for sch in st.session_state.schedules:
        if date_obj >= sch["start_date"] and wname in sch["days_of_week"]:
            for t in sch["times"]:
                occ.append({"date": date_obj, "name": sch["name"], "time": t})
    return sorted(occ, key=lambda x: x["time"])

def adherence_this_week(today):
    start = today - dt.timedelta(days=today.weekday())
    total = taken = 0
    for i in range(7):
        d = start + dt.timedelta(days=i)
        for ev in occurrences_for_date(d):
            total += 1
            if event_key(ev["date"], ev["name"], ev["time"]) in st.session_state.taken_events:
                taken += 1
    return int((taken / total) * 100) if total else 100

def draw_trophy():
    if not TURTLE_AVAILABLE:
        st.balloons()
        return
    # Simple fallback if turtle is available but we are on Streamlit Cloud
    st.balloons()

# ------------------------------
# Sidebar
# ------------------------------
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_minutes = st.slider(
        "Reminder window (minutes before dose)", 1, 60, st.session_state.reminder_minutes
    )

# ------------------------------
# Main layout
# ------------------------------
st.title("Pill MedTimer — Your Daily Medicine Companion")

col_input, col_main, col_side = st.columns([1.3, 1.7, 1.2])

# ------------------------------
# Input column – Add new schedule
# ------------------------------
with col_input:
    st.subheader("Add medicine schedule")
    choice = st.selectbox("Select medicine or choose 'Custom'", options=["Custom"] + COMMON_MEDICINES)
    med_name = st.text_input("Medicine name", value="" if choice == "Custom" else choice)

    today = dt.date.today()
    today_wname = weekday_name(today)

    days_selected = st.multiselect("Days of week", DAY_ORDER, default=[today_wname])
    dose_count = st.number_input("Doses per day", min_value=1, max_value=6, value=1, step=1)

    dose_times = []
    for i in range(dose_count):
        t = st.time_input(f"Dose time #{i+1}", value=dt.time(9 + i*3, 0), key=f"time_{i}")
        dose_times.append(t)

    start_date = st.date_input("Start date", value=today)

    if st.button("Add schedule"):
        final_name = med_name.strip() or choice
        if final_name and days_selected:
            st.session_state.schedules.append({
                "name": final_name,
                "days_of_week": days_selected,
                "times": dose_times,
                "start_date": start_date
            })
            st.success(f"Added schedule for **{final_name}**")
            st.rerun()
        else:
            st.warning("Please enter a medicine name and select at least one day.")

# ------------------------------
# Checklist column – Today's doses
# ------------------------------
with col_main:
    st.subheader("Today's checklist")
    now_dt = dt.datetime.now()
    now_time = now_dt.time()
    today = dt.date.today()

    events = occurrences_for_date(today)

    if not events:
        st.info("No doses scheduled for today. Enjoy your day!")
    else:
        for ev in events:
            key = event_key(ev["date"], ev["name"], ev["time"])
            taken = key in st.session_state.taken_events

            # Reminder logic
            dose_dt = dt.datetime.combine(ev["date"], ev["time"])
            minutes_until = (dose_dt - now_dt).total_seconds() / 60

            reminder_active = 0 < minutes_until <= st.session_state.reminder_minutes

            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                status = "✅ Taken" if taken else "⏰ Upcoming"
                st.write(f"**{ev['time'].strftime('%H:%M')}** – {ev['name']}  {status}")
            with col2:
                if reminder_active:
                    auto_beep()
                    st.markdown("<span class='pill pill-yellow'>Reminder!</span>", unsafe_allow_html=True)
                elif taken:
                    st.markdown("<span class='pill pill-green'>Done</span>", unsafe_allow_html=True)
                else:
                    st.empty()
            with col3:
                if not taken:
                    if st.button("Mark as taken", key=key):
                        mark_taken(ev["date"], ev["name"], ev["time"])

# ------------------------------
# Side column – Stats & motivation
# ------------------------------
with col_side:
    st.subheader("This week")
    adherence = adherence_this_week(today)
    st.metric("Adherence", f"{adherence}%")

    if adherence >= 90:
        st.success("Amazing consistency! 🏆")
        draw_trophy()
    elif adherence >= 70:
        st.info("Good job – keep going! 💪")
    else:
        st.warning("Let’s try to hit more doses this week!")

    st.caption(random.choice(QUOTES))

    if st.button("Clear all taken marks (reset week)"):
        st.session_state.taken_events = set()
        st.success("All marks cleared")
        st.rerun()
