import streamlit as st
from pathlib import Path

# =========================
# Page & brand
# =========================
st.set_page_config(page_title="Dream | MilkBox AI", page_icon="☁️", layout="wide")
LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

PRIMARY = "#18A999"   # teal
ACCENT  = "#57C785"   # MilkBox green (borders)
INK     = "#1F2937"   # text
MUTED   = "#6B7280"   # muted text
SOFTBG  = "#F7FAFC"

# =========================
# Pricing knobs (kept private)
# =========================
BASE_PLATFORM_FEE = 5.00
OPENAI_PER_1K_TOKENS = 0.006
EMAIL_PER_1K = 1.00
STORAGE_PER_GB = 0.25
TOOL_CATALOG = {
    "Auth/Login": 3.00,
    "Database (Supabase)": 5.00,
    "File Uploads": 2.50,
    "Analytics": 3.50,
    "Webhooks": 1.50,
    "Payments": 4.00,
    "Image Generation": 4.00,
    "Vector Search": 3.00,
}
HIDDEN_MARKUP_MULTIPLIER = 1.20  # not shown to users

# =========================
# Styles
# =========================
CSS = f"""
<style>
/* page */
.block-container {{ padding-top: 1.1rem !important; }}
body {{
  background: linear-gradient(180deg, {SOFTBG} 0%, #ECFEFF 100%);
}}
/* centered content wrapper */
.wrap {{
  max-width: 1120px;
  margin: 0 auto;
}}
.center {{ text-align:center; }}
/* cards */
.card {{
  border: 2px solid {ACCENT}55;
  background: #FFFFFF;
  border-radius: 16px;
  padding: 1rem 1.2rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.04);
}}
.card-tight {{ padding: .8rem 1rem; }}
h1.hx {{
  font-size: clamp(2rem, 4vw, 3.1rem);
  font-weight: 800;
  color: {INK};
  margin: .3rem 0 .6rem;
}}
.sub {{ color: {MUTED}; margin-bottom: 1rem; }}
.btn-primary {{
  background:{PRIMARY}; color:#fff; border:none; border-radius:12px; padding:.85rem 1.05rem;
}}
.badge {{
  background: #E9FEF4;
  color: {ACCENT};
  padding: .25rem .6rem;
  border-radius: 999px;
  font-size: .85rem;
  font-weight: 600;
}}
/* fix streamlit button width */
.stButton > button {{ width: 100%; }}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# =========================
# HERO (logo centered, no empty boxes)
# =========================
st.markdown('<div class="wrap">', unsafe_allow_html=True)

st.markdown('<div class="card center">', unsafe_allow_html=True)
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=160)

st.markdown('<h1 class="hx">☁️ Turn Your Dream Into an App</h1>', unsafe_allow_html=True)
st.markdown('<div class="sub">Answer 13 questions and your idea comes alive with MilkBox AI.</div>', unsafe_allow_html=True)

st.button("🌙 Start Dreaming", key="start_dreaming", use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)  # /card

st.write("")  # small spacing

# =========================
# HOW IT WORKS (centered; 3 items inside green cards)
# =========================
st.markdown('<h3 class="center">How It Works</h3>', unsafe_allow_html=True)
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🖼️ Upload Logo")
    st.write("Share your brand identity by uploading your logo.")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ❓ Answer 13 Questions")
    st.write("Quick steps that turn ideas into a clear, shippable plan.")
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ☁️ Get Your Mockup")
    st.write("We generate a beautiful preview — totally free. Code & deploy are paid.")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# =========================
# COST INDICATOR + CURRENCY (all inside cards, no markup details shown)
# =========================
st.markdown('<h3 class="center">Cost Indicator (estimate)</h3>', unsafe_allow_html=True)
left, right = st.columns([1.15, 0.85])

with left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    visits = st.slider("Monthly visitors", 100, 100_000, 2_000, step=100)
    tokens = st.slider("OpenAI usage (tokens / month)", 1_000, 5_000_000, 100_000, step=1_000)
    emails = st.slider("Transactional emails / month", 0, 100_000, 1_000, step=100)
    storage = st.slider("Storage (GB)", 0, 1_000, 10, step=1)
    addons = st.multiselect(
        "Add-on tools",
        options=list(TOOL_CATALOG.keys()),
        default=["Auth/Login", "Database (Supabase)"]
    )
    st.markdown('</div>', unsafe_allow_html=True)

with right:
    # compute USD total (markup included silently)
    openai_cost = (tokens / 1000) * OPENAI_PER_1K_TOKENS
    email_cost  = (emails / 1000) * EMAIL_PER_1K
    storage_cost = storage * STORAGE_PER_GB
    addons_cost = sum(TOOL_CATALOG[a] for a in addons)
    total_usd = (BASE_PLATFORM_FEE + openai_cost + email_cost + storage_cost + addons_cost) * HIDDEN_MARKUP_MULTIPLIER

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Currency**")
    currency = st.selectbox(
        "Choose currency",
        ["USD $", "ZAR R", "NGN ₦", "JPY ¥", "GBP £", "EUR €"],
        index=1,  # ZAR first for your audience; change as you like
        label_visibility="collapsed",
    )
    default_rates = {
        "USD $": 1.00,
        "ZAR R": 18.5,
        "NGN ₦": 1600.0,
        "JPY ¥": 155.0,
        "GBP £": 0.78,
        "EUR €": 0.92,
    }
    # allow manual override
    rate = st.number_input("Exchange rate vs USD (editable)", min_value=0.0001, value=float(default_rates[currency]), step=0.01)
    converted = total_usd * rate

    st.metric(f"Estimated Monthly ({currency})", f"{converted:,.2f}")
    st.caption("Estimates only. Adjust the sliders and exchange rate to fit your region.")
    st.markdown('</div>', unsafe_allow_html=True)

st.write("")

# =========================
# ACTIONS (inside green cards)
# =========================
st.markdown('<h3 class="center">Ready?</h3>', unsafe_allow_html=True)
a1, a2 = st.columns(2)
with a1:
    st.markdown('<div class="card card-tight">', unsafe_allow_html=True)
    if st.button("🧪 Generate Free Mockup", use_container_width=True):
        st.success("Mockup generated! (Preview only — no code yet.)")
    st.markdown('</div>', unsafe_allow_html=True)
with a2:
    st.markdown('<div class="card card-tight">', unsafe_allow_html=True)
    st.write("Deploying and running your app happens inside MilkBox AI after purchase.")
    st.link_button("➡️ Continue in MilkBoxAI", "https://milkboxai.onrender.com", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # /wrap
