import streamlit as st

def render():
    st.header("🍹 Bar Tools")

    st.subheader("ABV Calculator")
    c1, c2, c3 = st.columns(3)
    with c1:
        vol_ml = st.number_input("Volume (ml)", min_value=0.0, value=50.0, step=5.0)
    with c2:
        abv_pct = st.number_input("ABV (%)", min_value=0.0, max_value=100.0, value=40.0, step=0.5)
    with c3:
        density = st.number_input("Density (g/ml)", min_value=0.5, max_value=2.0, value=0.789, step=0.001,
                                  help="Ethanol density ≈ 0.789 g/ml; water ≈ 1.0 g/ml")

    alcohol_ml = vol_ml * (abv_pct / 100.0)
    alcohol_g  = alcohol_ml * density
    st.caption("Result updates live as you type.")
    st.metric("Pure alcohol (ml)", f"{alcohol_ml:,.2f}")
    st.metric("Pure alcohol (g)", f"{alcohol_g:,.2f}")

    st.divider()

    st.subheader("Tip / Split Calculator")
    with st.form("tip_split"):
        bill = st.number_input("Bill total", min_value=0.0, value=100.0, step=1.0)
        tip_pct = st.slider("Tip %", 0, 30, 10)
        people = st.number_input("People", min_value=1, value=2, step=1)
        submitted = st.form_submit_button("Calculate")

    if submitted:
        tip  = bill * (tip_pct / 100.0)
        total = bill + tip
        per_person = total / max(people, 1)
        c1, c2, c3 = st.columns(3)
        c1.metric("Tip", f"{tip:,.2f}")
        c2.metric("Total", f"{total:,.2f}")
        c3.metric("Per person", f"{per_person:,.2f}")

    st.caption("This is a starter stub. We can add unit conversions, recipe scalers, etc.")
