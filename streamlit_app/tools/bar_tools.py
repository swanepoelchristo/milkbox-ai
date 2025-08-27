import math
import streamlit as st

DENSITY_ETHANOL_G_PER_ML = 0.789  # 0.789 g/ml @ ~20°C

def fmt_money(x: float, currency: str = "$") -> str:
    try:
        return f"{currency}{x:,.2f}"
    except Exception:
        return f"{x:.2f}"

def fmt_num(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}"

def abv_calculator():
    st.subheader("🍸 ABV / Pure Alcohol Calculator")

    with st.form("abv_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            volume_ml = st.number_input("Drink volume (ml)", min_value=0.0, value=330.0, step=10.0)
        with col2:
            abv_pct = st.number_input("ABV (%)", min_value=0.0, max_value=100.0, value=5.0, step=0.1)

        col3, col4 = st.columns(2)
        with col3:
            servings = st.number_input("Number of servings", min_value=1, value=1, step=1)
        with col4:
            region = st.selectbox(
                "Standard drink definition",
                options=["EU (10 g)", "US (14 g)"],
                index=0,
            )

        submitted = st.form_submit_button("Calculate")

    if not submitted:
        st.info("Enter your values and click **Calculate**.")
        return

    total_ml = volume_ml * servings
    pure_alcohol_ml = total_ml * (abv_pct / 100.0)
    pure_alcohol_g = pure_alcohol_ml * DENSITY_ETHANOL_G_PER_ML

    std_g = 10.0 if "EU" in region else 14.0
    std_drinks = pure_alcohol_g / std_g

    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Total volume", f"{fmt_num(total_ml)} ml")
    with colB:
        st.metric("Pure alcohol (ml)", f"{fmt_num(pure_alcohol_ml)} ml")
    with colC:
        st.metric("Pure alcohol (g)", f"{fmt_num(pure_alcohol_g)} g")

    st.metric("Estimated standard drinks", fmt_num(std_drinks, 2), help=f"Based on {region}")

    share = (
        f"ABV calc — {servings}× {fmt_num(volume_ml)} ml @ {fmt_num(abv_pct)}% ABV\n"
        f"Pure alcohol: {fmt_num(pure_alcohol_ml)} ml ({fmt_num(pure_alcohol_g)} g)\n"
        f"Standard drinks ({region}): {fmt_num(std_drinks)}"
    )

    st.write("**Share/Copy:**")
    st.text_area("Copy the result", value=share, height=96, label_visibility="collapsed")

def tip_splitter():
    st.subheader("🧾 Tip & Bill Split")

    with st.form("tip_form", clear_on_submit=False):
        bill = st.number_input("Bill amount", min_value=0.0, value=100.00, step=1.0)
        tip_pct = st.number_input("Tip (%)", min_value=0.0, value=10.0, step=1.0)
        people = st.number_input("Number of people", min_value=1, value=2, step=1)
        currency = st.text_input("Currency symbol", value="$")
        submitted = st.form_submit_button("Split it")

    if not submitted:
        st.info("Enter your values and click **Split it**.")
        return

    tip_amount = bill * (tip_pct / 100.0)
    total_with_tip = bill + tip_amount
    per_person = total_with_tip / people

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Tip amount", fmt_money(tip_amount, currency))
    with col2:
        st.metric("Total with tip", fmt_money(total_with_tip, currency))
    with col3:
        st.metric("Per person", fmt_money(per_person, currency))

    share = (
        f"Bill split — Bill {fmt_money(bill, currency)}, Tip {fmt_num(tip_pct)}%, People {people}\n"
        f"Tip: {fmt_money(tip_amount, currency)}\n"
        f"Total: {fmt_money(total_with_tip, currency)}\n"
        f"Each: {fmt_money(per_person, currency)}"
    )

    st.write("**Share/Copy:**")
    st.text_area("Copy the result", value=share, height=96, label_visibility="collapsed")

def render():
    st.header("🍹 Bar Tools (ABV & Tips)")
    st.caption("Fast, mobile-friendly helpers for bartenders & hosts.")

    tabs = st.tabs(["ABV Calculator", "Tip & Bill Split"])
    with tabs[0]:
        abv_calculator()
    with tabs[1]:
        tip_splitter()

# Allow local run for quick dev
if __name__ == "__main__":
    st.set_page_config(page_title="Bar Tools", page_icon="🍹", layout="centered")
    render()

