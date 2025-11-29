# app.py
import streamlit as st
import pandas as pd
import datetime as dt
import random

# Optional: Turtle graphics for local use
try:
    import turtle
    TURTLE_AVAILABLE = True
except:
    TURTLE_AVAILABLE = False

# ------------------------------
# Config
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
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        font-size: 18px;
        border-radius: 8px;
        padding: 0.5rem 1rem;
    }
    .stTextInput>div>div>input {
        font-size: 18px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------
# Session state
# ------------------------------
if "medicines" not in st.session_state:
    st.session_state.medicines = []
if "taken_today" not in st.session_state:
    st.session_state.taken_today = set()
if "motivational_quotes" not in st.session_state:
    st.session_state.motivational_quotes = [
        "Every dose taken is a step toward wellness.",
        "Consistency builds strength.",
        "You're doing great—keep it up!",
        "Health is the real wealth.",
        "Small steps lead to big changes.",
        "Your effort today shapes your tomorrow.",
        "Peace of mind starts with care.",
        "One dose at a time, you're healing.",
        "You're not alone—MedTimer is here for you.",
        "Celebrate every dose taken!"
    ]
# Full medicine list (can be expanded)
ALL_MEDICINES = sorted([
    "Aspirin", "Amoxicillin", "Azithromycin", "Atorvastatin", "Acetaminophen", "Albuterol",
    "Baclofen", "Bisoprolol", "Bupropion", "Betamethasone",
    "Ciprofloxacin", "Cetirizine", "Clonazepam", "Citalopram", "Chlorpheniramine",
    "Doxycycline", "Dexamethasone", "Diazepam", "Digoxin",
    "Erythromycin", "Escitalopram", "Esomeprazole",
    "Furosemide", "Fluoxetine", "Famotidine",
    "Gabapentin", "Glimepiride", "Gliclazide",
    "Hydrochlorothiazide", "Hydroxyzine", "Hydrocortisone",
    "Ibuprofen", "Insulin", "Indomethacin", "Ivermectin", "Imatinib",
    "Levothyroxine", "Lisinopril", "Losartan", "Loratadine",
    "Metformin", "Montelukast", "Metoprolol", "Methylprednisolone",
    "Naproxen", "Nifedipine", "Nitroglycerin", "Nortriptyline",
    "Omeprazole", "Ondansetron", "Olanzapine",
    "Paracetamol", "Pantoprazole", "Prednisone", "Propranolol",
    "Quetiapine", "Quinapril",
    "Ranitidine", "Risperidone", "Rosuvastatin",
    "Sertraline", "Simvastatin", "Salbutamol",
    "Tramadol", "Tamsulosin", "Terbinafine",
    "Ursodiol", "Ulipristal",
    "Valacyclovir", "Venlafaxine", "Vitamin D",
    "Warfarin", "Wellbutrin",
    "Zolpidem", "Zinc Supplement", "Zopiclone"
])

# Autocomplete input
st.subheader("Add Medicine")
typed_name = st.text_input("Start typing medicine name", placeholder="e.g., in, an, met...")

# Filter suggestions
suggestions = [m for m in ALL_MEDICINES if m.lower().startswith(typed_name.lower())] if typed_name else []

if suggestions:
    selected_med = st.selectbox("Select from suggestions", options=suggestions)
    med_time = st.time_input("Scheduled Time", value=dt.time(9, 0))
    if st.button("Add to Schedule"):
        add_medicine(selected_med, med_time)
        st.success(f"Added {selected_med} at {med_time.strftime('%H:%M')}")
else:
    st.info("Type at least 1–2 letters to see suggestions.")
    

# ------------------------------
# Turtle graphics
# ------------------------------
def draw_trophy():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("MedTimer: Weekly Trophy!")
    t = turtle.Turtle()
    t.speed(3)
    t.pensize(3)

    # Cup
    t.color("orange")
    t.begin_fill()
    t.circle(40)
    t.end_fill()

    # Base
    t.penup()
    t.goto(-20, -60)
    t.pendown()
    t.begin_fill()
    t.forward(40)
    t.right(90)
    t.forward(20)
    t.right(90)
    t.forward(40)
    t.right(90)
    t.forward(20)
    t.end_fill()

    # Text
    t.penup()
    t.goto(0, -100)
    t.write("🏆 Great Adherence!", align="center", font=("Arial", 14, "bold"))
    t.hideturtle()

# ------------------------------
# Functions
# ------------------------------
def add_medicine(name, time):
    st.session_state.medicines.append({
        "name": name,
        "time": time,
        "taken": False,
        "date": dt.date.today()
    })

def mark_taken(name):
    for med in st.session_state.medicines:
        if med["name"] == name and med["date"] == dt.date.today():
            med["taken"] = True
            st.session_state.taken_today.add(name)

def calculate_adherence():
    today = dt.date.today()
    week_start = today - dt.timedelta(days=today.weekday())
    week_meds = [m for m in st.session_state.medicines if week_start <= m["date"] <= today]
    if not week_meds:
        return 0
    taken = sum(1 for m in week_meds if m["taken"])
    return int((taken / len(week_meds)) * 100)

# ------------------------------
# Layout
# ------------------------------
st.title("💊 MedTimer — Daily Medicine Companion")
st.write("Track your daily medicines, mark doses, and celebrate your adherence with friendly visuals.")

col_input, col_checklist, col_side = st.columns([1.2, 1.5, 1.3])

# ------------------------------
# Input column
# ------------------------------
with col_input:
    st.subheader("Add Medicine")
    med_name = st.selectbox("Medicine Name", options=st.session_state.medicine_options)
    med_time = st.time_input("Scheduled Time", value=dt.time(9, 0))
    if st.button("Add to Schedule"):
        add_medicine(med_name, med_time)
        st.success(f"Added {med_name} at {med_time.strftime('%H:%M')}")

# ------------------------------
# Checklist column
# ------------------------------
with col_checklist:
    st.subheader("Today's Checklist")
    now = dt.datetime.now().time()
    today_meds = [m for m in st.session_state.medicines if m["date"] == dt.date.today()]
    if not today_meds:
        st.info("No medicines scheduled for today.")
    else:
        for med in today_meds:
            status = "upcoming"
            if med["taken"]:
                status = "taken"
            elif now > med["time"]:
                status = "missed"

            color = {"taken": "green", "upcoming": "orange", "missed": "red"}[status]
            st.markdown(f"**{med['name']}** at {med['time'].strftime('%H:%M')} — "
                        f"<span style='color:{color};font-weight:bold'>{status.upper()}</span>",
                        unsafe_allow_html=True)
            if not med["taken"] and status != "missed":
                if st.button(f"Mark {med['name']} as taken"):
                    mark_taken(med["name"])
                    st.success(f"{med['name']} marked as taken.")

# ------------------------------
# Side column
# ------------------------------
with col_side:
    st.subheader("Weekly Adherence Score")
    score = calculate_adherence()
    st.metric("Adherence", f"{score}%")

    if score >= 80:
        st.success("🎉 Excellent adherence this week!")
        draw_trophy()
    elif score >= 50:
        st.info("👍 Good job! Keep going.")
    else:
        st.warning("⚠️ Let's aim for better consistency.")

    st.markdown("---")
    st.subheader("Motivational Tip")
    st.info(random.choice(st.session_state.motivational_quotes))

# ------------------------------
# Footer
# ------------------------------
st.markdown("---")
st.caption("MedTimer is designed for simplicity, clarity, and encouragement. Turtle graphics open in a separate window locally.")
