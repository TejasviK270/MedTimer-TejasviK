# app.py
import streamlit as st
import pandas as pd
import datetime as dt
import random
import math

# Turtle is not supported inside Streamlit's web canvas.
# This import allows local turtle window pop-ups when running the app locally.
# On Streamlit Cloud, the turtle part may not render, but the rest of the app will work.
try:
    import turtle
    TURTLE_AVAILABLE = True
except Exception:
    TURTLE_AVAILABLE = False


# ------------------------------
# Config & styling
# ------------------------------
st.set_page_config(
    page_title="ShopImpact - Conscious Shopping Dashboard",
    page_icon="🌿",
    layout="wide"
)

EARTHY_COLORS = {
    "bg": "#F6F4EE",
    "green": "#2E7D32",
    "blue": "#1565C0",
    "beige": "#D7CCC8",
    "brown": "#6D4C41",
    "accent": "#4CAF50",
    "warn": "#F9A825"
}

def apply_earthy_theme():
    st.markdown(
        f"""
        <style>
            .main {{
                background-color: {EARTHY_COLORS['bg']};
            }}
            h1, h2, h3, h4 {{
                color: {EARTHY_COLORS['green']};
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            }}
            .stButton>button {{
                background-color: {EARTHY_COLORS['green']};
                color: white;
                border-radius: 8px;
                font-size: 16px;
                padding: 0.5rem 1rem;
            }}
            .eco-card {{
                background: #ffffff;
                border: 1px solid {EARTHY_COLORS['beige']};
                border-radius: 10px;
                padding: 1rem;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )

apply_earthy_theme()


# ------------------------------
# Data: Multipliers & alternatives & eco tips
# ------------------------------
PRODUCT_MULTIPLIERS = {
    # higher = higher estimated CO₂ impact per currency unit
    "Leather Shoes": 2.0,
    "Fast Fashion Top": 1.3,
    "Second-hand Clothes": 0.4,
    "Organic Cotton Shirt": 0.6,
    "Bamboo Toothbrush": 0.2,
    "Reusable Bottle": 0.1,
    "Electronics (New)": 2.5,
    "Electronics (Refurbished)": 1.0,
    "Local Produce": 0.3,
    "Imported Produce": 1.1,
}

GREENER_ALTERNATIVES = {
    "Leather Shoes": ["Vegan leather shoes (Brand: XGreen)", "Second-hand leather (local thrift)"],
    "Fast Fashion Top": ["Organic cotton top (Brand: PureWear)", "Second-hand top (ThriftHub)"],
    "Second-hand Clothes": ["Keep going! Explore high-quality thrift (ThriftHub)", "Upcycled fashion (ReCraft)"],
    "Organic Cotton Shirt": ["Hemp blend shirt (EcoHemp)", "Fair-trade organic cotton (KindCotton)"],
    "Bamboo Toothbrush": ["Compostable bamboo brush (LeafSmile)", "Recycled plastic brush (BlueCycle)"],
    "Reusable Bottle": ["Steel insulated bottle (GreenSip)", "Glass bottle (EcoHydrate)"],
    "Electronics (New)": ["Refurbished device (ReTech)", "Repair old device (FixIt Local)"],
    "Electronics (Refurbished)": ["Maintain and repair to extend life (FixIt Local)", "Trade-in upgrade (ReTech)"],
    "Local Produce": ["Seasonal local produce (Farm2Table)", "Organic local farms (SoilKind)"],
    "Imported Produce": ["Local seasonal alternatives (Farm2Table)", "Frozen local when out of season (CoolLocal)"],
}

ECO_TIPS = [
    "Did you know? Choosing refurbished electronics can cut footprint dramatically.",
    "Bamboo grows fast and needs fewer inputs—great low-impact choice.",
    "Refill and reuse: a reusable bottle saves plastic and CO₂ over time.",
    "Local and seasonal produce reduce transport emissions.",
    "Second-hand first: extending a product’s life is a powerful climate action.",
    "Organic cotton reduces pesticide use and can lower environmental impact.",
    "Repair before replacing—your wallet and the planet thank you.",
    "Choose timeless designs to avoid fast fashion churn.",
    "Plan purchases and avoid impulse buys to reduce waste.",
    "Check for fair-trade labels—ethical brands often have lower footprints."
]


# ------------------------------
# Session state initialization
# ------------------------------
if "purchases" not in st.session_state:
    st.session_state.purchases = []  # list of dicts
if "eco_badges" not in st.session_state:
    st.session_state.eco_badges = []  # badges earned strings
if "monthly_target" not in st.session_state:
    st.session_state.monthly_target = 200.0  # arbitrary target for CO₂ score (lower is better)
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False


# ------------------------------
# Utility functions
# ------------------------------
def calculate_impact(price: float, product_type: str) -> float:
    multiplier = PRODUCT_MULTIPLIERS.get(product_type, 1.0)
    return price * multiplier

def add_purchase(product_type: str, brand: str, price: float, date: dt.date):
    impact = calculate_impact(price, product_type)
    entry = {
        "product_type": product_type,
        "brand": brand.strip(),
        "price": price,
        "impact": impact,
        "date": date,
        "month": dt.date(date.year, date.month, 1)
    }
    st.session_state.purchases.append(entry)
    return entry

def award_badges(month: dt.date, df_month: pd.DataFrame):
    total_impact = df_month["impact"].sum() if not df_month.empty else 0.0
    total_spend = df_month["price"].sum() if not df_month.empty else 0.0

    newly_awarded = []

    # Eco Saver: total impact under target
    if total_impact <= st.session_state.monthly_target:
        newly_awarded.append("Eco Saver")

    # Low Impact Shopper: average impact per purchase < 0.8
    if not df_month.empty and (df_month["impact"].mean() < 0.8):
        newly_awarded.append("Low Impact Shopper")

    # Ethical Explorer: bought at least 2 greener product types
    greener_count = sum(
        1 for p in set(df_month["product_type"].tolist())
        if PRODUCT_MULTIPLIERS.get(p, 1.0) <= 0.6
    )
    if greener_count >= 2:
        newly_awarded.append("Ethical Explorer")

    # Avoid duplicates
    for b in newly_awarded:
        if b not in st.session_state.eco_badges:
            st.session_state.eco_badges.append(b)

    return newly_awarded

def get_month_dataframe(month: dt.date) -> pd.DataFrame:
    if not st.session_state.purchases:
        return pd.DataFrame(columns=["product_type", "brand", "price", "impact", "date", "month"])
    df = pd.DataFrame(st.session_state.purchases)
    return df[df["month"] == dt.date(month.year, month.month, 1)]

def suggest_alternatives(product_type: str):
    return GREENER_ALTERNATIVES.get(product_type, ["Explore local second-hand options", "Repair/Refurbish to extend life"])

def random_tip():
    return random.choice(ECO_TIPS)

def positive_choice(product_type: str) -> bool:
    # A simplistic rule: products with multiplier <= 0.6 are considered eco-friendly choices
    return PRODUCT_MULTIPLIERS.get(product_type, 1.0) <= 0.6


# ------------------------------
# Turtle Graphics (local-only)
# ------------------------------
def draw_leaf():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("ShopImpact: Eco Leaf")
    t = turtle.Turtle()
    t.speed(3)
    t.color("green")
    t.pensize(3)

    # Leaf shape
    t.begin_fill()
    t.fillcolor("light green")
    t.circle(50, 90)
    t.circle(50, -180)
    t.circle(50, 90)
    t.end_fill()

    # Stem
    t.right(90)
    t.forward(60)

    # Text
    t.penup()
    t.left(90)
    t.forward(20)
    t.write("Great eco choice!", align="center", font=("Arial", 14, "bold"))
    t.hideturtle()

def draw_badge():
    if not TURTLE_AVAILABLE:
        return
    screen = turtle.Screen()
    screen.title("ShopImpact: Eco Badge")
    t = turtle.Turtle()
    t.speed(3)
    t.color("brown")
    t.pensize(3)

    # Circle badge
    t.begin_fill()
    t.fillcolor("#FFD54F")  # warm yellow
    t.circle(60)
    t.end_fill()

    # Star in center
    t.penup()
    t.sety(-20)
    t.pendown()
    t.color("#2E7D32")
    for _ in range(5):
        t.forward(80)
        t.right(144)

    # Text
    t.penup()
    t.sety(20)
    t.write("Eco Saver!", align="center", font=("Arial", 14, "bold"))
    t.hideturtle()


# ------------------------------
# Sidebar (controls)
# ------------------------------
with st.sidebar:
    st.header("Settings")
    st.slider("Monthly CO₂ target (lower is stricter)", min_value=50.0, max_value=500.0, value=st.session_state.monthly_target, step=10.0, key="monthly_target")
    st.toggle("High-contrast / Dark mode", value=st.session_state.dark_mode, key="dark_mode")

    st.markdown("---")
    st.subheader("About")
    st.caption("ShopImpact helps you see the environmental estimate of purchases and nudges greener choices. Turtle graphics open in a separate window locally.")


# ------------------------------
# Layout: Inputs & dashboard
# ------------------------------
st.title("ShopImpact — Conscious Shopping Dashboard 🌿")
st.write("Track purchases, estimate CO₂ impact, earn badges, and discover greener alternatives. Make sustainability visible and rewarding.")

col_input, col_dashboard, col_right = st.columns([1.1, 1.6, 1.2])


# ------------------------------
# Input column
# ------------------------------
with col_input:
    st.markdown("### Add a purchase")
    product_type = st.selectbox("Product Type", options=list(PRODUCT_MULTIPLIERS.keys()))
    brand = st.text_input("Brand", placeholder="e.g., EcoHemp")
    price = st.number_input("Price", min_value=0.0, step=10.0, value=0.0)
    date = st.date_input("Purchase Date", value=dt.date.today())

    if st.button("Log Purchase"):
        if price <= 0.0 or not brand.strip():
            st.warning("Please enter a valid price and brand.")
        else:
            entry = add_purchase(product_type, brand, price, date)
            st.success(f"Added: {entry['product_type']} ({entry['brand']}) — ₹{entry['price']:.2f} | Impact: {entry['impact']:.2f}")
            st.info(f"Suggestion: {', '.join(suggest_alternatives(product_type))}")
            st.write(f"Tip: {random_tip()}")

            # Trigger turtle graphics for positive choices
            if positive_choice(product_type):
                st.toast("Eco-friendly choice detected — opening a leaf turtle graphic locally.")
                draw_leaf()


# ------------------------------
# Dashboard column
# ------------------------------
with col_dashboard:
    st.markdown("### Monthly dashboard")
    # Month picker derived from current or last purchase month
    today_month = dt.date(dt.date.today().year, dt.date.today().month, 1)
    months_available = sorted({p["month"] for p in st.session_state.purchases}) or [today_month]
    month_choice = st.selectbox("Select month", options=months_available, format_func=lambda d: d.strftime("%b %Y"))

    df_month = get_month_dataframe(month_choice)

    if df_month.empty:
        st.info("No purchases for this month yet. Start logging to see your dashboard.")
    else:
        total_spend = float(df_month["price"].sum())
        total_impact = float(df_month["impact"].sum())
        avg_impact = float(df_month["impact"].mean())
        count = int(df_month.shape[0])

        # Summary cards
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Purchases", count)
        with c2:
            st.metric("Total spend (₹)", f"{total_spend:,.2f}")
        with c3:
            st.metric("Estimated CO₂ impact", f"{total_impact:,.2f}")
        with c4:
            st.metric("Avg impact per item", f"{avg_impact:.2f}")

        # Award badges for the chosen month
        new_badges = award_badges(month_choice, df_month)
        if new_badges:
            st.success(f"New badges earned: {', '.join(new_badges)}")
            # Celebrate with turtle badge if Eco Saver included
            if "Eco Saver" in new_badges:
                st.toast("Badge earned — opening a turtle badge window locally.")
                draw_badge()

        # Charts
        st.markdown("#### Impact by product type")
        by_type = df_month.groupby("product_type")[["price", "impact"]].sum().sort_values("impact", ascending=False)
        st.bar_chart(by_type["impact"])

        st.markdown("#### Purchases table")
        st.dataframe(
            df_month[["date", "product_type", "brand", "price", "impact"]].sort_values("date"),
            use_container_width=True
        )

        # Simple gauge-like progress for monthly impact target
        st.markdown("#### Monthly impact vs target")
        progress_ratio = min(1.0, total_impact / float(st.session_state.monthly_target))
        st.progress(progress_ratio, text=f"Impact {total_impact:.2f} / Target {st.session_state.monthly_target:.2f}")

        if total_impact <= st.session_state.monthly_target:
            st.markdown(
                f"<div class='eco-card'>"
                f"<b style='color:{EARTHY_COLORS['accent']}'>Great job!</b> You're within your target this month. Keep it up with local, second-hand, and refurbished picks."
                f"</div>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<div class='eco-card'>"
                f"<b style='color:{EARTHY_COLORS['warn']}'>Heads-up:</b> You've exceeded your target. Try alternatives like refurbished electronics or local produce to reduce impact."
                f"</div>",
                unsafe_allow_html=True
            )


# ------------------------------
# Right column: badges, suggestions, tips
# ------------------------------
with col_right:
    st.markdown("### Badges & nudges")
    if not st.session_state.eco_badges:
        st.info("No badges yet — choose greener options to unlock them.")
    else:
        for b in st.session_state.eco_badges:
            st.success(f"🏅 {b}")

    st.markdown("#### Greener alternatives by your recent product")
    if st.session_state.purchases:
        last_product = st.session_state.purchases[-1]["product_type"]
        alts = suggest_alternatives(last_product)
        for a in alts:
            st.write(f"• {a}")
    else:
        st.write("Log a purchase to see tailored alternatives.")

    st.markdown("#### Motivational tip")
    st.write(random_tip())

    st.markdown("---")
    st.caption("Note: Turtle drawings appear in a separate local window and may not render on Streamlit Cloud.")


# ------------------------------
# Footer actions
# ------------------------------
st.markdown("---")
cA, cB = st.columns([1, 2])
with cA:
    if st.button("Export current month as CSV"):
        if not st.session_state.purchases:
            st.warning("No data to export.")
        else:
            df = get_month_dataframe(month_choice)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("Download CSV", data=csv, file_name=f"shopimpact_{month_choice.strftime('%Y_%m')}.csv", mime="text/csv")

with cB:
    st.caption("Keep experimenting: add dark mode, more tips, and fun turtle animations locally.")
