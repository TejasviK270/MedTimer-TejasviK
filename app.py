# app.py
import streamlit as st
import datetime as dt
import random
import math
import struct

# Optional: Turtle graphics (local only)
try:
    import turtle
    TURTLE_AVAILABLE = True
except:
    TURTLE_AVAILABLE = False

# ------------------------------
# App config
# ------------------------------
st.set_page_config(page_title="MedTimer Companion", page_icon="💊", layout="wide")

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
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 16px;
        border-radius: 8px;
        padding: 0.45rem 0.9rem;
        border: none;
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
# Data and state
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

if "schedules" not in st.session_state:
    st.session_state.schedules = []
if "taken_events" not in st.session_state:
    st.session_state.taken_events = set()
if "reminder_minutes" not in st.session_state:
    st.session_state.reminder_minutes = 15
if "trigger_rerun" not in st.session_state:
    st.session_state.trigger_rerun = False

# ------------------------------
# Audio beep
# ------------------------------
def generate_beep(duration_sec=0.3, freq_hz=880, sample_rate=44100, volume=0.4) -> bytes:
    n_samples = int(duration_sec * sample_rate)
    data = bytearray()
    def _le32(x): return struct.pack("<I", x)
    def _le16(x): return struct.pack("<H", x)
    byte_rate = sample_rate * 2
    block_align = 2
    data_chunk_size = n_samples * 2
    header = b"RIFF" + _le32(36 + data_chunk_size) + b"WAVE"
    fmt = b"fmt " + _le32(16) + _le16(1) + _le16(1) + _le32(sample_rate) + _le32(byte_rate) + _le16(block_align) + _le16(16)
    data_hdr = b"data" + _le32(data_chunk_size)
    for i in range(n_samples):
        t = i / sample_rate
        sample = int(32767 * volume * math.sin(2 * math.pi * freq_hz * t))
        data += struct.pack("<h", sample)
    return header + fmt + data_hdr + data

def maybe_beep():
    st.audio(generate_beep(), format="audio/wav")

# ------------------------------
# Helpers
# ------------------------------
def weekday_name(date_obj: dt.date) -> str:
    return DAY_ORDER[date_obj.weekday()]

def event_key(date_obj: dt.date, name: str, time_obj: dt.time) -> str:
    return f"{date_obj.isoformat()}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(date_obj: dt.date, name: str, time_obj: dt.time):
    st.session_state.taken_events.add(event_key(date_obj, name, time_obj))

def occurrences_for_date(date_obj: dt.date):
    wname = weekday_name(date_obj)
    occ = []
    for sch in st.session_state.schedules:
        if date_obj >= sch["start_date"] and wname in sch["days_of_week"]:
            for t in sch["times"]:
                occ.append({"date": date_obj, "name": sch["name"], "time": t})
    return sorted(occ, key=lambda x: x["time"])

def adherence_this_week(today: dt.date) -> int:
    start = today - dt.timedelta(days=today.weekday())
    total = 0
    taken = 0
    for i in range(7):
        d = start + dt.timedelta(days=i)
        for ev in occurrences_for_date(d):
            total += 1
            if event_key(ev["date"], ev["name"], ev["time"]) in st.session_state.taken_events:
                taken += 1
    return int((taken / total) * 100) if total else 0

def draw_trophy():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("MedTimer: Weekly Trophy!")
    t = turtle.Turtle()
    t.speed(3)
    t.pensize(3)
    t.color("orange")
    t.begin_fill()
    t.circle(40)
    t.end_fill()
    t.penup()
    t.goto(-20, -60)
    t.pendown()
    t.begin_fill()
    for _ in range(2):
        t.forward(40)
        t.right(90)
        t.forward(20)
        t.right(90)
    t.end_fill()
    t.penup()
    t.goto(0, -100)
    t.write("🏆 Great Adherence!", align="center", font=("Arial", 14, "bold"))
    t.hideturtle()

# ------------------------------
# Layout
# ------------------------------
st.title("💊 MedTimer — Daily Medicine Companion")

col_input, col_main, col_side = st.columns([1.3, 1.7, 1.2])

# ------------------------------
# Input column
# ------------------------------
with col_input:
    st.subheader("Add medicine schedule")
    choice = st.selectbox("Select medicine or choose 'Custom'", options=["Custom"] + COMMON_MEDICINES)
    med_name = st.text_input("Enter medicine name", value="" if choice == "Custom" else choice)
    today = dt.date.today()
    today_wname = weekday_name(today)
    days_selected = st.multiselect("Days of week", DAY_ORDER, default=[today_wname])
    dose_count = st.number_input("Doses per day", min_value=1, max_value=6, value=1)
    dose_times = [st.time_input(f"Dose time #{i+1}", value=dt.time(9+i*3,0), key=f"time_{i}") for i in range(dose_count)]
    start_date = st.date_input("Start date", value=today)
    if st.button("Add schedule"):
        if med_name.strip() and days_selected:
            st.session_state.schedules.append({
                "name": med_name.strip(),
                "days_of_week": days_selected,
                "times": dose_times,
                "start_date": start_date
            })
            st.success(f"Added schedule for {med_name}")
        else:
            st.warning("Please enter a valid name and select days.")

# ------------------------------
# Checklist column
# ------------------------------
with col_main:
    st.subheader("Today's checklist")
    now = dt.datetime.now().time()
    events = occurrences_for_date(today)
    for i, ev in enumerate(events):
        key = event_key(ev["date"], ev["name"], ev["time"])
        if key in st.session_state.taken_events:
            status
