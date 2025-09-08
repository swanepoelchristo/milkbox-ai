import time
import streamlit as st

def app():
    st.title("🧰 My Tool")
    st.caption("Starter template with inputs, options, upload, and a Run button.")

    # --- Sidebar options (remove anything you don't need) ---
    with st.sidebar:
        st.markdown("### Options")
        mode = st.radio("Mode", ["Quick", "Advanced"], horizontal=True)
        section_hint = st.selectbox("Section (tools.yaml)", ["Free", "Pro", "Demos"], index=0)
        st.info("Tweak or delete these controls as you like.", icon="🛠️")

    # --- Main form ---
    with st.form(key="my_tool_form", clear_on_submit=False):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Your name", placeholder="Ada Lovelace")
        with col2:
            count = st.number_input("Repeat how many times?", min_value=1, max_value=10, value=3)

        message = st.text_area("Message", placeholder="Type something…")
        uploaded = st.file_uploader("Optional .txt file", type=["txt"])
        run = st.form_submit_button("Run", use_container_width=True)

    if run:
        try:
            text = (message or "").strip()
            if uploaded is not None:
                text_from_file = uploaded.getvalue().decode("utf-8", errors="ignore")
                text = f"{text}\n{text_from_file}" if text else text_from_file

            with st.spinner("Working…"):
                time.sleep(0.6)  # simulate a bit of work
                result = _process(text=text or "Hello", count=int(count))

            st.success("Done! 🎉")
            st.write("### Output")
            st.code(result, language="text")

            with st.expander("Debug / Context"):
                st.write(
                    {
                        "mode": mode,
                        "section_hint": section_hint,
                        "name": name,
                        "chars_in_message": len(text),
                    }
                )
        except Exception as e:
            st.error(f"Something went wrong: {e}")

@st.cache_data(show_spinner=False)
def _process(text: str, count: int) -> str:
    """Tiny demo processor: repeat the input N times."""
    return " ".join([text] * count)
