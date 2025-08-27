import streamlit as st

def render():
    st.header("🍸 Bar Tools (ABV & Tips)")
    st.write("Two quick helpers for bars: 1) ABV calculator (volume × ABV% → pure alcohol ml/g) "
             "and 2) Tip & bill split calculator. Keep it lightweight, fast, and mobile-friendly.")

    st.subheader("ABV Calculator")
    col1, col2 = st.columns(2)
    with col1:
        volume = st.number_input("Drink volume (ml)", min_value=0.0, value=500.0)
    with col2:
        abv = st.number_input("ABV (%)", min_value=0.0, value=5.0)

    if st.button("Calculate ABV"):
        pure_alcohol = volume * (abv / 100.0)
        st.success(f"🍺 Pure alcohol content: {pure_alcohol:.1f} ml")

    st.markdown("---")

    st.subheader("Tip & Bill Split")
    amount = st.number_input("Bill amount", min_value=0.0, value=100.0)
    tip_percent = st.slider("Tip %", 0, 30, 10)
    people = st.number_input("Number of people", min_value=1, value=2)

    if st.button("Split Bill"):
        total = amount * (1 + tip_percent / 100.0)
        per_person = total / people
        st.success(f"💵 Total: {total:.2f} | Each person pays: {per_person:.2f}")
