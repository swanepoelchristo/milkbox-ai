import streamlit as st
from pathlib import Path

# -------------------------
# Branding / Config
# -------------------------
st.set_page_config(page_title="Dream | MilkBox AI", page_icon="☁️", layout="wide")

LOGO_PATH = Path(__file__).resolve().parent.parent / "assets" / "logo.png"

PRIMARY = "#18A999"     # teal
ACCENT  = "#57C785"     # warm green
INK     = "#1F2937"     # slate-800
MUTED   = "#6B7280"     # slate-500
SURFACE = "#FFFFFF"
SOFTBG  = "#F7FAFC"

# ---- Hidden pricing knobs (tune these anytime) ----
BASE_PLATFORM_FEE = 5.00         # your monthly base
OPENAI_PER_1K_TOKENS = 0.006     # rough gpt-4o-mini style placeholder
EMAIL_PER_1K = 1.00              # transactional emails
STORAGE_PER_GB = 0.25            # storage
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
HIDDEN_MARKUP_MULTIPLIER = 1.20   # 20% markup baked in

# -------------------------
# Simple CSS (clouds + cards)
# -------------------------
CLOUD_CSS = f"""
<style>
/* App background */
.reportview-container .main .block-container {{
  padding-top: 1.2rem;
}}
body {{
  background: linear-gradient(180deg, {SOFTBG} 0%, #ECFEFF 100%);
}}

/* subtle cloud svg behind hero */
.hero {{
  position: relative;
  padding: 2.5rem 1rem 2rem 1rem;
  border-radius: 16px;
  background: rgba(255,255,255,0.75);
  box-shadow: 0 8px 30px rgba(0,0,0,0.05);
  overflow: hidden;
}}
.hero:before {{
  content: "";
  position: absolute;
  inset: -60px -60px auto -60px;
  height: 260px;
  background: url('data:image/svg+xml;utf8,\
  <svg xmlns="http://www.w3.org/2000/svg" width="1200" height="260" viewBox="0 0 1200 260">\
  <g fill="%23E6FAF4" opacity="0.9">\
  <ellipse cx="180" cy="150" rx="180" ry="80"/>\
  <ellipse cx="420" cy="120" rx="220" ry="90"/>\
  <ellipse cx="760" cy="150" rx="240" ry="95"/>\
  <ellipse cx="1040" cy="130" rx="200" ry="85"/>\
  </g></svg>') no-repeat center/cover;
  filter: blur(0.5px);
  z-index: 0;
}}

/* center logo */
.logo-wrap {{ text-align:center; }}
.logo-wrap img {{ border-radius: 16px; }}

.h1 {{
  font-size: clamp(2rem, 3.8vw, 3.2rem);
  font-weight: 800;
  color: {INK};
  text-align:center;
  margin: .2rem 0 0.6rem;
}}
.sub {{
  color: {MUTED};
  text-align:center;
  margin-bottom: 1rem;
}}

.buttons {{ display:flex; gap:.75rem; justify-content:center; flex-wrap:wrap; }}
.btn {{
  padding: .7rem 1rem;
  border-radius: 12px;
  border: 1px solid rgba(0,0,0,0.05);
  background: white;
  cursor: pointer;
}}
.btn-primary {{
  background: {PRIMARY};
  color: white;
  border: none;
}}
.badge {{
  background: #E9FEF4;
  color: {ACCENT};
  padding: .25rem .6rem;
  border-radius: 999px;
  font-size: .85rem;
  font-weight: 600;
}}

.card {{
  border: 1px solid #EEF2F7;
  background: {SURFACE};
  border-radius: 16px;
  padding: 1rem;
  box-shadow: 0 6px 18px rgba(0,0,0,0.04);
}}
.card h3 {{ margin:.5rem 0 .25rem; }}
.card p  {{ color: {MUTED}; margin:0; }}

.pricing .card h2 {{ margin:0 0 .25rem; }}
.price {{ font-size: 1.8rem; font-weight: 800; color: {INK}; }}
.small  {{ color: {MUTED}; font-size: .9rem; }}
</style>
"""
st.markdown(CLOUD_CSS, unsafe_allow_html=True)

# -------------------------
# HERO
# -------------------------
with st.container():
    st.markdown('<div class="hero">', unsafe_allow_html=True)

    # centered logo
    if LOGO_PATH.exists():
        st.markdown('<div class="logo-wrap">', unsafe_allow_html=True)
        st.image(str(LOGO_PATH), width=140)
        st.markdown('</div>', unsafe_allow_html=True)

    # cloud emoji, not star; dreamy vibe
    st.markdown('<div class="h1">☁️ Turn Your Dream Into an App</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub">Answer 13 questions and your idea comes alive with MilkBox AI.</div>', unsafe_allow_html=True)

    # buttons (Start Dreaming, How it works)
    colA, colB = st.columns([1,1])
    with colA:
        start = st.button("🌙 Start Dreaming", use_container_width=True)
    with colB:
        st.page_link("pages/1_Dream.py", label="☁️ See how it works", icon=None)

    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# HOW IT WORKS — 3 friendly cards
# -------------------------
st.markdown("### How It Works")
c1, c2, c3 = st.columns(3)
with c1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🖼️ Upload Logo")
    st.markdown("<p>Share your brand identity by uploading your logo.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### ❓ Answer 13 Questions")
    st.markdown("<p>Quick steps that turn ideas into a clear, shippable plan.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
with c3:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🎉 Get Your Mockup")
    st.markdown("<p>We generate a beautiful mockup preview — totally free.</p>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# -------------------------
# COST INDICATOR (live)
# -------------------------
st.markdown("### Cost Indicator (estimate)")
st.caption("Dream is free. Building & deploying the working app is paid — estimate below updates in real time.")

colL, colR = st.columns([1.1,1])
with colL:
    visits = st.slider("Monthly visitors", 100, 100_000, 2000, step=100)
    tokens = st.slider("OpenAI usage (tokens / month)", 1_000, 5_000_000, 100_000, step=1_000)
    emails = st.slider("Transactional emails / month", 0, 100_000, 1000, step=100)
    storage = st.slider("Storage (GB)", 0, 1000, 10, step=1)

    addons = st.multiselect(
        "Add-on tools",
        options=list(TOOL_CATALOG.keys()),
        default=["Auth/Login", "Database (Supabase)"]
    )

with colR:
    # cost math (transparent + hidden markup)
    openai_cost = (tokens / 1000) * OPENAI_PER_1K_TOKENS
    email_cost  = (emails / 1000) * EMAIL_PER_1K
    storage_cost = storage * STORAGE_PER_GB
    addons_cost = sum(TOOL_CATALOG[a] for a in addons)

    raw_total = BASE_PLATFORM_FEE + openai_cost + email_cost + storage_cost + addons_cost
    final_total = raw_total * HIDDEN_MARKUP_MULTIPLIER

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### Estimated Monthly Cost")
    st.metric("Total (with fees & markup)", f"${final_total:,.2f}")
    st.write("Breakdown (before markup):")
    st.write(
        f"- Base platform: **${BASE_PLATFORM_FEE:.2f}**\n"
        f"- OpenAI: **${openai_cost:,.2f}**\n"
        f"- Emails: **${email_cost:,.2f}**\n"
        f"- Storage: **${storage_cost:,.2f}**\n"
        f"- Add-ons: **${addons_cost:,.2f}**"
    )
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# -------------------------
# CALLS TO ACTION (free vs paid gate)
# -------------------------
st.markdown("### Ready?")
col1, col2 = st.columns([1,1])
with col1:
    if st.button("🧪 Generate Free Mockup", use_container_width=True):
        st.success("Mockup generated! (Preview only — no code yet.)")
with col2:
    if st.button("🔒 Deploy to War Room", use_container_width=True):
        st.info("Deploying requires a paid plan. Choose a plan below to unlock War Room access.")

st.divider()

# -------------------------
# PRICING (cards)
# -------------------------
st.markdown("### Choose Your Plan")
p1, p2, p3 = st.columns(3)
with p1:
    st.markdown('<div class="card pricing">', unsafe_allow_html=True)
    st.markdown("#### Starter")
    st.markdown('<div class="price">Free</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Generate a single mockup</div>', unsafe_allow_html=True)
    st.button("Get Started", key="starter_btn", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with p2:
    st.markdown('<div class="card pricing">', unsafe_allow_html=True)
    st.markdown("#### Pro ☁️")
    st.markdown('<div class="price">$25/mo</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Unlimited mockups • Custom templates • Priority support</div>', unsafe_allow_html=True)
    st.button("Go Pro", key="pro_btn", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with p3:
    st.markdown('<div class="card pricing">', unsafe_allow_html=True)
    st.markdown("#### Enterprise")
    st.markdown('<div class="price">Let’s talk</div>', unsafe_allow_html=True)
    st.markdown('<div class="small">Dedicated AI agents • SSO • SLA</div>', unsafe_allow_html=True)
    st.button("Contact Sales", key="ent_btn", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.caption("Note: War Room access unlocks after purchase. Dream stays free forever.")
