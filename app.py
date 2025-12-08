import streamlit as st
import datetime as dt
import random, math, struct

# Page config
st.set_page_config(page_title="MedTimer", page_icon="Pill", layout="wide")

# Custom CSS
st.markdown("""
<style>
    body {background:#f8fdff; font-family: 'Segoe UI', sans-serif;}
    .big-title {font-size: 2.8rem !important; color: #00695c; text-align: center; margin-bottom: 10px;}
    .pill {padding: 8px 16px; border-radius: 50px; font-weight: bold; color: white; display: inline-block; margin: 5px 0;}
    .pill-green {background: #2e7d32;}
    .pill-yellow {background: #f9a825; color: black;}
    .pill-red {background: #c62828;}
    .dose-box {background: #e8f5e9; padding: 15px; border-radius: 12px; border-left: 5px solid #4caf50; margin: 10px 0;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
for key, value in [("schedules", []), ("taken_events", set()), ("reminder_min", 15)]:
    if key not in st.session_state:
        st.session_state[key] = value

# Helper functions
def key(date, name, time_obj):
    return f"{date}|{name}|{time_obj.strftime('%H:%M')}"

def mark_taken(d, n, t):
    st.session_state.taken_events.add(key(d, n, t))
    st.success(f"Marked: {n} at {t.strftime('%I:%M %p')} as taken!")
    st.rerun()

def beep():
    try:
        s, f, dur = 44100, 880, 0.4
        data = bytearray()
        for i in range(int(s * dur)):
            v = int(32767 * 0.5 * math.sin(2 * math.pi * f * i / s))
            data += struct.pack("<h", v)
        header = (b"RIFF" + struct.pack("<I", 36+len(data)) + b"WAVEfmt " +
                  struct.pack("<IHHIIHH", 16, 1, 1, s, s*2, 2, 16) + b"data" + struct.pack("<I", len(data)))
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

# Sidebar
with st.sidebar:
    st.header("Settings")
    st.session_state.reminder_min = st.slider("Reminder before", 1, 60, st.session_state.reminder_min, help="Beep when dose is due soon")
    if st.button("Clear All Taken Records", type="secondary"):
        st.session_state.taken_events = set()
        st.rerun()

# Main App
st.markdown("<h1 class='big-title'>Pill MedTimer</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align:center; color:#555;'>Never miss a dose again!</p>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1.6, 2, 1.2])

# === ADD MEDICINE ===
with col1:
    st.subheader("Add New Medicine")
    
    with st.form("add_medicine", clear_on_submit=True):
        name = st.text_input("Medicine Name", placeholder="e.g., Metformin 500mg")
        days = st.multiselect("Repeat on", 
            ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            default=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
        
        st.write("**Dose Times** (add one by one)")
        if "dose_times" not in st.session_state:
            st.session_state.dose_times = [dt.time(8, 0)]  # Default: one dose at 8:00 AM
        
        # Display current doses
        for i, t in enumerate(st.session_state.dose_times):
            col_a, col_b = st.columns([3, 1])
            with col_a:
                new_time = st.time_input(f"Dose {i+1}", value=t, key=f"input_{i}")
                st.session_state.dose_times[i] = new_time
            with col_b:
                if st.button("Remove", key=f"remove_{i}"):
                    st.session_state.dose_times.pop(i)
                    st.rerun()

        # Add new dose button
        col_add1, col_add2 = st.columns([2, 2])
        with col_add1:
            if st.button("Add Another Dose Time"):
                st.session_state.dose_times.append(dt.time(18, 0))  # default evening
                st.rerun()

        submitted = st.form_submit_button("Save Medicine Schedule")
        if submitted and name and st.session_state.dose_times:
            st.session_state.schedules.append({
                "name": name,
                "days": days,
                "times": st.session_state.dose_times.copy(),
                "start_date": dt.date.today()
            })
            st.success(f"{name} added with {len(st.session_state.dose_times)} dose(s)!")
            st.session_state.dose_times = [dt.time(8, 0)]  # reset form
            st.rerun()

# === TODAY'S DOSES ===
with col2:
    st.subheader(f"Today's Doses – {dt.date.today():%A, %b %d}")
    events = get_today_events()
    now = dt.datetime.now()

    if not events:
        st.info("No doses scheduled today. Rest well!")
    else:
        for e in events:
            event_dt = dt.datetime.combine(dt.date.today(), e["time"])
            mins_to = (event_dt - now).total_seconds() / 60
            k = key(dt.date.today(), e["name"], e["time"])
            taken = k in st.session_state.taken_events

            with st.container():
                st.markdown(f"<div class='dose-box'>", unsafe_allow_html=True)
                col_a, col_b, col_c = st.columns([2.5, 2, 1.5])
                
                with col_a:
                    st.write(f"**{e['time'].strftime('%I:%M %p')}**")
                    st.write(f"**{e['name']}**")

                with col_b:
                    if taken:
                        st.markdown("<span class='pill pill-green'>Taken</span>", unsafe_allow_html=True)
                    elif mins_to <= 0:
                        st.markdown("<span class='pill pill-red'>Missed</span>", unsafe_allow_html=True)
                    elif mins_to <= st.session_state.reminder_min:
                        beep()
                        st.markdown("<span class='pill pill-yellow'>TAKE NOW</span>", unsafe_allow_html=True)
                    else:
                        mins = int(mins_to)
                        st.caption(f"In {mins} min" if mins < 60 else f"In {mins//60}h {mins%60}m")

                with col_c:
                    if not taken:
                        if st.button("Mark Taken", key=k, type="primary"):
                            mark_taken(dt.date.today(), e["name"], e["time"])
                    else:
                        st.markdown("**Taken**")

                st.markdown("</div>", unsafe_allow_html=True)
                st.markdown("---")

# === WEEKLY STATS ===
with col3:
    st.subheader("7-Day Adherence")
    
    expected = taken_cnt = 0
    today = dt.date.today()
    
    for i in range(7):
        day = today - dt.timedelta(days=i)
        wd = day.strftime("%A")
        prefix = f"{day}|"
        
        for s in st.session_state.schedules:
            if day >= s.get("start_date", day) and any(d in s["days"] for d in [wd, wd[:3]]):
                expected += len(s["times"])
        
        for tk in st.session_state.taken_events:
            if tk.startswith(prefix):
                taken_cnt += 1

    adherence = int(100 * taken_cnt / expected) if expected > 0 else 100
    
    st.metric("Adherence Rate", f"{adherence}%")
    
    if adherence >= 95:
        st.balloons()
    elif adherence >= 80:
        st.success("Great consistency!")
    elif adherence >= 60:
        st.warning("Keep pushing!")
    else:
        st.error("Time to get back on track!")

    st.caption(random.choice([
        "You're crushing it!",
        "Every dose counts!",
        "Health = discipline + love",
        "Proud of your effort!",
        "Consistency wins!"
    ]))

    if st.button("Reset All Records"):
        st.session_state.taken_events = set()
        st.rerun()
