import streamlit as st
import datetime as dt
import random, math, struct

# Page config
st.set_page_config(page_title="MedTimer", page_icon="Pill", layout="wide")
st.markdown("""
<style>
    body {background:#F0F8FF; color:#004d40; font-size:18px}
    h1,h2,h3 {color:#00695C}
    .pill {padding:6px 14px; border-radius:999px; font-weight:700; color:white; margin:4px;}
    .pill-green {background:#2E7D32}
    .pill-yellow {background:#FBC02D; color:#000}
    .pill-red {background:#C62828}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if "schedules" not in st.session_state: st.session_state.schedules = []
if "taken_events" not in st.session_state: st.session_state.taken_events = set()
if "reminder_minutes" not in st.session_state: st.session_state.reminder_minutes = 15

# Helper functions
def key(date, name, time_obj):
    return f"{date}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(date, name, time_obj):
    st.session_state.taken_events.add(key(date, name, time_obj))
    st.success(f"Marked: {name} at {time_obj.strftime('%H:%M')} as taken!")
    st.rerun()

def beep():
    try:
        sample_rate = 44100
        duration = 0.4
        freq = 880
        samples = int(sample_rate * duration)
        data = bytearray()
        for i in range(samples):
            value = int(32767 * 0.5 * math.sin(2 * math.pi * freq * i / sample_rate))
            data += struct.pack("<h", value)
        header = (b"RIFF" + struct.pack("<I", 36+len(data)) + b"WAVEfmt " +
                  struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate*2, 2, 16) +
                  b"data" + struct.pack("<I", len(data)))
        st.audio(header + data, format="audio/wav", autoplay=True)
    except:
        pass  # In case audio fails on some environments

def get_today_events():
    today = dt.date.today()
    weekday = today.strftime("%A")
    events = []
    for s in st.session_state.schedules:
        if today >= s["start_date"] and any(d in s["days_of_week"] for d in [weekday, weekday[:3]]):
            for t in s["times"]:
                events.append({"name": s["name"], "time": t})
    return sorted(events, key=lambda x: x["time"])

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_minutes = st.slider("Reminder before (minutes)", 1, 60, st.session_state.reminder_minutes)
    if st.button("Clear all taken records"):
        st.session_state.taken_events = set()
        st.success("All records cleared!")
        st.rerun()

# Main title
st.title("Pill MedTimer – Never Miss a Dose")

col1, col2, col3 = st.columns([1.5, 2, 1.2])

# === Add New Medicine ===
with col1:
    st.subheader("Add New Medicine")
    with st.form("add_med"):
        name = st.text_input("Medicine Name", placeholder="e.g., Vitamin D")
        days = st.multiselect("Repeat on", 
            ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        doses = st.slider("Doses per day", 1, 6, 2)
        times = []
        for i in range(doses):
            t = st.time_input(f"Dose {i+1} time", value=dt.time(8 + i*4), key=f"newtime{i}")
            times.append(t)
        
        submitted = st.form_submit_button("Add Schedule")
        if submitted and name:
            st.session_state.schedules.append({
                "name": name,
                "days_of_week": days,
                "times": times,
                "start_date": dt.date.today()
            })
            st.success(f"{name} added!")
            st.rerun()

# === Today's Schedule ===
with col2:
    st.subheader(f"Today's Schedule – {dt.date.today().strftime('%A, %B %d')}")
    events = get_today_events()
    now = dt.datetime.now()

    if not events:
        st.info("No medications scheduled for today. Enjoy your day!")
    else:
        for event in events:
            event_dt = dt.datetime.combine(dt.date.today(), event["time"])
            mins_until = (event_dt - now).total_seconds() / 60
            k = key(dt.date.today(), event["name"], event["time"])
            is_taken = k in st.session_state.taken_events

            # Layout per medication
            a, b, c = st.columns([3, 1.5, 1.5])
            
            with a:
                status_icon = "Taken" if is_taken else "Pending"
                st.write(f"**{event['time'].strftime('%I:%M %p')}** – {event['name']}")
            
            with b:
                if is_taken:
                    st.markdown("<span class='pill pill-green'>DONE</span>", unsafe_allow_html=True)
                elif mins_until <= 0:
                    st.markdown("<span class='pill pill-red'>MISSED</span>", unsafe_allow_html=True)
                elif mins_until <= st.session_state.reminder_minutes:
                    beep()
                    st.markdown("<span class='pill pill-yellow'>TAKE NOW</span>", unsafe_allow_html=True)
                else:
                    remaining = int(mins_until)
                    st.caption(f"In {remaining} min" if remaining < 60 else f"In {remaining//60}h {remaining%60}m")

            with c:
                if is_taken:
                    st.success("Taken")
                else:
                    if st.button("Mark as Taken", key=k):
                        mark_taken(dt.date.today(), event["name"], event["time"])

# === Weekly Stats ===
with col3:
    st.subheader("7-Day Adherence")
    
    expected = taken_count = 0
    today = dt.date.today()
    
    for days_back in range(7):
        day = today - dt.timedelta(days=days_back)
        weekday = day.strftime("%A")
        day_prefix = f"{day}|"
        
        for s in st.session_state.schedules:
            if day >= s["start_date"] and any(d in s["days_of_week"] for d in [weekday, weekday[:3]]):
                expected += len(s["times"])
        
        for taken_key in st.session_state.taken_events:
            if taken_key.startswith(day_prefix):
                taken_count += 1

    adherence = int(taken_count / expected * 100) if expected > 0 else 100

    st.metric("Adherence Rate", f"{adherence}%", delta=None)
    
    if adherence >= 95:
        st.balloons()
    elif adherence >= 80:
        st.success("Good job!")
    elif adherence >= 60:
        st.warning("Room for improvement")
    else:
        st.error("Let's get back on track!")

    st.caption(random.choice([
        "Consistency is key!", "You're doing great!", "Every dose counts!",
        "Health is wealth", "Keep it up!", "Proud of you!"
    ]))

    if st.button("Reset All Taken Records", type="secondary"):
        st.session_state.taken_events.clear()
        st.rerun()
