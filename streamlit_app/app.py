import streamlit as st
from io import BytesIO
from textwrap import dedent
import datetime as _dt

# -------------------------
# Milkbox AI Dashboard v2
# -------------------------
st.set_page_config(page_title="Milkbox AI", page_icon="🥛", layout="wide")

st.title("🥛 Milkbox AI Dashboard")
st.caption("Prototype shelf for Milkbox tools — CV Builder demo included.")

# ========== SIDEBAR ==========
st.sidebar.header("🧰 Tools")
tool = st.sidebar.radio(
    "Pick a tool",
    ["CV Builder (demo)", "Invoice Generator (coming soon)", "Bush Pig (coming soon)", "Bar Menu (coming soon)"],
    index=0,
)

# Global settings
st.sidebar.header("⚙️ Settings")
theme = st.sidebar.selectbox("Theme", ["Auto", "Light", "Dark"], index=0)
lang_en = st.sidebar.checkbox("English", value=True)
lang_af = st.sidebar.checkbox("Afrikaans", value=False)

# ========== LAYOUT ==========
col1, col2 = st.columns([2, 1])

# ============================
# 1) CV BUILDER – WORKING DEMO
# ============================
if tool.startswith("CV Builder"):
    with col1:
        st.subheader("📄 CV Builder")
        st.write("Fill in the form. Preview updates live. Download as **Markdown**.")

        with st.form("cv_form", clear_on_submit=False):
            # Header
            name = st.text_input("Full name", placeholder="Jane Doe")
            title = st.text_input("Professional title", placeholder="Data Analyst")
            email = st.text_input("Email", placeholder="jane@example.com")
            phone = st.text_input("Phone", placeholder="+27 82 555 1234")
            location = st.text_input("Location", placeholder="Cape Town, South Africa")
            website = st.text_input("Website / LinkedIn", placeholder="https://linkedin.com/in/janedoe")

            # Summary
            st.markdown("**Summary**")
            summary = st.text_area(
                "Brief summary",
                height=100,
                placeholder="Analytical problem-solver with 5+ years experience turning messy data into clear decisions.",
            )

            # Skills
            st.markdown("**Skills (comma-separated)**")
            skills_raw = st.text_input("Skills", placeholder="Python, SQL, Power BI, Excel, Communication")

            # Experience
            st.markdown("**Experience**")
            n_roles = st.number_input("Number of roles", 1, 6, 2)
            roles = []
            for i in range(int(n_roles)):
                st.markdown(f"**Role {i+1}**")
                r_title = st.text_input(f"Role {i+1} – Job Title", key=f"rt{i}", placeholder="Data Analyst")
                r_company = st.text_input(f"Role {i+1} – Company", key=f"rc{i}", placeholder="Acme Ltd")
                r_dates = st.text_input(f"Role {i+1} – Dates", key=f"rd{i}", placeholder="2022–Present")
                r_bullets = st.text_area(
                    f"Role {i+1} – Bullet points (one per line)",
                    key=f"rb{i}",
                    height=80,
                    placeholder="• Built automated sales dashboards\n• Reduced reporting time by 60%",
                )
                roles.append((r_title, r_company, r_dates, r_bullets))

            # Education
            st.markdown("**Education**")
            edu = st.text_area(
                "Education (free text)",
                height=80,
                placeholder="BCom (Information Systems), University of Cape Town, 2018",
            )

            submitted = st.form_submit_button("🔧 Build CV")

        # Build Markdown (also updates even if not pressed, thanks to Streamlit's state)
        def _to_markdown():
            skills = [s.strip() for s in skills_raw.split(",") if s.strip()]
            today = _dt.datetime.now().date().isoformat()

            md = f"# {name or 'Your Name'}\n\n"
            contact_line = " • ".join(
                [x for x in [title, email, phone, location, website] if x]
            )
            if contact_line:
                md += contact_line + "\n\n"

            if summary:
                md += "## Summary\n" + summary.strip() + "\n\n"

            if skills:
                md += "## Skills\n"
                md += ", ".join(skills) + "\n\n"

            md += "## Experience\n"
            for (rt, rc, rd, rb) in roles:
                if not (rt or rc or rd or rb):
                    continue
                line = f"**{rt or 'Job Title'}**, {rc or 'Company'} · _{rd or 'Dates'}_\n\n"
                # Normalize bullets
                bullets = [b.strip("• ").strip() for b in rb.splitlines() if b.strip()]
                if bullets:
                    line += "\n".join([f"- {b}" for b in bullets]) + "\n\n"
                md += line

            if edu:
                md += "## Education\n" + edu.strip() + "\n\n"

            md += f"---\n_Created with Milkbox AI · {today}_\n"
            return dedent(md)

        md_text = _to_markdown()

        st.markdown("### 👀 Live Preview")
        st.markdown(md_text)

    with col2:
        st.subheader("⬇️ Download")
        buf = BytesIO(md_text.encode("utf-8"))
        st.download_button(
            label="Download CV (Markdown)",
            data=buf,
            file_name=f"{(name or 'cv').lower().replace(' ', '_')}.md",
            mime="text/markdown",
        )

        st.divider()
        st.subheader("📊 Status")
        st.metric("Fields Completed", sum(bool(x) for x in [name, title, email, phone, location, website, summary]))
        st.metric("Roles Added", int(n_roles))
        st.success("CV Builder ready")

# ============================
# PLACEHOLDERS for other tools
# ============================
else:
    with col1:
        st.subheader("Coming soon")
        st.info("This tool is a placeholder for now. The CV Builder is fully working.")

    with col2:
        st.subheader("Status")
        st.write("Nothing to configure yet.")
        st.caption("Switch to *CV Builder (demo)* in the sidebar to test a working tool.")

# Footer
st.markdown("---")
st.caption("Milk Roads AI © 2025 | Prototype build")
