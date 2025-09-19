import streamlit as st
from pathlib import Path

# -------------------------
# Page + brand
# -------------------------
st.set_page_config(page_title="Dream | MilkBox AI", page_icon="☁️", layout="wide")

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

# brand colors (tweak anytime)
PRIMARY = "#18A999"     # teal
ACCENT  = "#57C785"     # milkbox green for borders
INK     = "#1F2937"     # dark text
MUTED   = "#6B7280"
SOFTBG  = "#F7FAFC"

# -------------------------
# $$ knobs (your economics)
# -------------------------
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

# your hidden markup
HIDDEN_MARKUP_MULTIPLIER = 1.20

# -------------------------
# simple CSS (center logo, green borders, soft clouds)
# -------------------------
CLOUD_CSS = f"""
<style>
body {{
  background: linear-gradient(180deg, {SOFTBG} 0%, #ECFEFF 100%);
}}
.block-container {{ padding-top: 1.2rem !important; }}

/* hero box */
.hero {{
  position: relative;
  padding: 2rem 1rem 1.25rem 1rem;
  border-radius: 18px;
  background: rgba(255,255,255,0.9);
  box-shadow: 0 10px 24px rgba(0,0,0,0.06);
  overflow: hidden;
  border: 2px solid {ACCENT}22;
}}
.hero:before {{
  content: "";
  position: absolute;
  inset: -60px -60px auto -60px;
  height: 240px;
  background: url('data:image/svg+xml;utf8,\
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260">\
  <g fill="%23E6FAF4" opacity="0.95">\
  <ellipse cx="180" cy="150" rx="180" ry="80"/>\
  <ellipse cx="420" cy="120" rx="220" ry="90"/>\
  <ellipse cx="760" cy="150" rx="240" ry="95"/>\
  <ellipse cx="1040" cy="130" rx="200" ry="85"/>\
  </g></svg>') no-repeat center/cover;
  z-index: 0;
}}

.logo-center {{ text-align:center; }}
.logo-center img {{ border-radius: 16px; }}

.h1 {{
  font-size: clamp(2rem, 3.8vw, 3.2rem);
  font-weight: 800;
  color: {INK};
  text-align:center;
  margin: .35rem 0 .5rem;
}}
.sub {{ color: {MUTED}; text-align:center; margin-bottom: .5rem; }}

.card {{
  border: 2px solid {ACCENT}55;     /* green border */
  background: #FFFFFF;
  border-radius: 16px;
  padding: 1rem 1.1rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.04);
}}
.card h3 {{ margin:.25rem 0 .25rem; }}
.card p  {{ color: {MUTED}; margin:0; }}

.badge {{
  background: #E9FEF4;
  color: {ACCENT};
  padding: .25rem .6rem;
  border-radius: 999px;
  font-size: .85rem;
  font-weight: 600;
}}
.btn-primary {{
  background:{PRIMARY}; color:#fff; border:none; border-radius:12px; padding:.8rem 1rem;
}}
</style>
"""
st.markdown(CLOUD_CSS, unsafe_allow_html=True)

# -------------------------
# HERO (centered logo + cloud vibe)
# -------------------------
st.markdown('<div class="hero">', unsafe_allow_html=True)
st.markdown('<div class="logo-center">', unsafe_allow_html=True)
if LOGO_PATH.exists():
    st.image(str(LOGO_PATH), width=160)
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="h1">☁️ Turn Your Dream Into an App</div>', unsafe_allow_html=True)
st.markdown('<div class="sub">Answer 13 questions and your idea comes alive with MilkBox AI.</div>', unsafe_allow_html=True)

# "Start Dreaming" (we keep it here; real flow stays in Dream)
start_col = st.container()
with start_col:
    st.button("🌙 Start Dreaming", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)  # /hero
st.markdown("")

# -------------------------
# HOW IT WORKS — 3 green cards
# -------------------------
st.markdown("#### How It Works")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🖼️ Upload Logo")
    st.markdown("Share your brand identity by uploading your logo.")
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ❓ Answer 13 Questions")
    st.markdown("Quick steps that turn ideas into a clear, shippable plan.")
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ☁️ Get Your Mockup")
    st.markdown("We generate a beautiful preview — totally free. Code & deploy are paid.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# -------------------------
# COST INDICATOR (with currency converter)
# -------------------------
st.markdown("#### Cost Indicator (estimate)")
wrapL, wrapR = st.columns([1.2, 0.8])

with wrapL:
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

with wrapR:
    # math in USD
    openai_cost = (tokens / 1000) * OPENAI_PER_1K_TOKENS
    email_cost  = (emails / 1000) * EMAIL_PER_1K
    storage_cost = storage * STORAGE_PER_GB
    addons_cost = sum(TOOL_CATALOG[a] for a in addons)
    raw_total_usd = BASE_PLATFORM_FEE + openai_cost + email_cost + storage_cost + addons_cost
    total_usd = raw_total_usd * HIDDEN_MARKUP_MULTIPLIER

    # currency map (editable rates; user can override)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Currency**")
    currency = st.selectbox(
        "Choose currency", 
        ["USD $", "ZAR R", "NGN ₦", "JPY ¥", "GBP £", "EUR €"],
        index=0,
        label_visibility="collapsed"
    )
    default_rates = {
        "USD $": 1.00,
        "ZAR R": 18.5,
        "NGN ₦": 1600.0,
        "JPY ¥": 155.0,
        "GBP £": 0.78,
        "EUR €": 0.92,
    }
    rate = st.number_input("Exchange rate vs USD (editable)", min_value=0.0001, value=float(default_rates[currency]), step=0.01)
    converted = total_usd * rate

    st.metric(f"Estimated Monthly ({currency})", f"{converted:,.2f}")
    with st.expander("Breakdown (USD, before markup)"):
        st.write(
            f"- Base platform: **${BASE_PLATFORM_FEE:.2f}**"
            f"\n- OpenAI: **${openai_cost:,.2f}**"
            f"\n- Emails: **${email_cost:,.2f}**"
            f"\n- Storage: **${storage_cost:,.2f}**"
            f"\n- Add-ons: **${addons_cost:,.2f}**"
            f"\n- Markup multiplier: **×{HIDDEN_MARKUP_MULTIPLIER:.2f}**"
        )
    st.caption("Rates are estimates; you can adjust the exchange rate above.")
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("")

# -------------------------
# ACTIONS (mockup free, deploy gated → jump to MilkBoxAI)
# -------------------------
st.markdown("#### Ready?")
ctaL, ctaR = st.columns([1,1])

with ctaL:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if st.button("🧪 Generate Free Mockup", use_container_width=True):
        st.success("Mockup generated! (Preview only — no code yet.)")
    st.markdown('</div>', unsafe_allow_html=True)

with ctaR:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("**Deploy & Plans**")
    st.caption("Deploying and running your app happens inside MilkBoxAI after purchase.")
    # for now, route to the app home; later this can open a dedicated plans/checkout screen
    if st.link_button("➡️ Continue in MilkBoxAI", "https://milkboxai.onrender.com", use_container_width=True):
        pass
    st.markdown('</div>', unsafe_allow_html=True)
