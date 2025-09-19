import streamlit as st

# --- Logo at top (optional if you want logo.png from assets) ---
st.image("streamlit_app/assets/logo.png", width=180)

# --- Hero Section ---
st.markdown(
    """
    # 🌟 Turn Your Dream Into an App
    Answer 13 questions and your idea comes alive with MilkBox AI.
    """
)
if st.button("🚀 Start Dreaming"):
    st.switch_page("pages/2_War_Room.py")  # example, adjust to your next step

st.divider()

# --- How It Works ---
st.subheader("How It Works")
cols = st.columns(3)
with cols[0]:
    st.markdown("### 🖼️ Upload Logo\nShare your brand identity by uploading your logo.")
with cols[1]:
    st.markdown("### ❓ Answer 13 Questions\nQuickly describe your dream idea step by step.")
with cols[2]:
    st.markdown("### 🎉 Get Your App\nWatch as MilkBox AI generates your starter app.")

st.divider()

# --- Testimonials ---
st.subheader("What Our Dreamers Say")
cols = st.columns(3)
with cols[0]:
    st.markdown("> ⭐⭐⭐⭐⭐\nMilkBox AI transformed my idea in days! — *Sanele D.*")
with cols[1]:
    st.markdown("> ⭐⭐⭐⭐⭐\nThe process was so easy — love the 13Q system! — *Marco R.*")
with cols[2]:
    st.markdown("> ⭐⭐⭐⭐⭐\nFaster than I imagined. Game changer. — *Emily W.*")

st.divider()

# --- Pricing Plans ---
st.subheader("Choose Your Plan")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Starter\nPerfect for getting started\n- Up to 3 apps\n- Basic templates\n\n💲 **Free**")
    st.button("Get Started", key="starter")

with col2:
    st.markdown("### Pro 🚀\nMost popular\n- Unlimited apps\n- Custom templates\n- Priority support\n\n💲 **$25/mo**")
    st.button("Go Pro", key="pro")

with col3:
    st.markdown("### Enterprise\nFor big teams\n- Everything in Pro\n- Dedicated AI agents\n- Premium support\n\n💲 **Contact us**")
    st.button("Contact Sales", key="enterprise")
