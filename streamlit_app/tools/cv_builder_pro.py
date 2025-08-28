import io
from pathlib import Path
import streamlit as st

# Optional deps for exports
try:
    from docx import Document  # python-docx
except Exception:
    Document = None

try:
    from reportlab.pdfgen import canvas  # reportlab
except Exception:
    canvas = None


def _render_header():
    st.header("🌍 International CV Builder (Pro)")
    st.caption("Pro templates, locale rules, advanced formatting, and premium exports.")


def _input_section():
    st.subheader("Candidate")
    name = st.text_input("Full name", value="")
    email = st.text_input("Email", value="")
    phone = st.text_input("Phone", value="")
    location = st.text_input("Location / Country", value="")

    st.subheader("Summary")
    summary = st.text_area("Professional summary")

    st.subheader("Experience (quick)")
    exp = st.text_area(
        "Experience (bullets, one per line)",
        placeholder="- Senior Designer at ACME (2022–now)\n- Led X, improved Y",
        height=120,
    )

    st.subheader("Skills")
    skills = st.text_area("Skills (comma-separated)", placeholder="Figma, SQL, Leadership")

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "location": location,
        "summary": summary,
        "experience": [ln.strip() for ln in exp.splitlines() if ln.strip()],
        "skills": [s.strip() for s in skills.split(",") if s.strip()],
    }


def _export_docx(data) -> bytes:
    if Document is None:
        raise RuntimeError("python-docx not installed")
    doc = Document()
    doc.add_heading(data["name"] or "Candidate", level=0)

    contact_bits = [x for x in (data["email"], data["phone"], data["location"]) if x]
    if contact_bits:
        doc.add_paragraph(" · ".join(contact_bits))

    if data["summary"]:
        doc.add_heading("Summary", level=2)
        doc.add_paragraph(data["summary"])

    if data["experience"]:
        doc.add_heading("Experience", level=2)
        for b in data["experience"]:
            doc.add_paragraph(b, style="List Bullet")

    if data["skills"]:
        doc.add_heading("Skills", level=2)
        doc.add_paragraph(", ".join(data["skills"]))

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _export_pdf(data) -> bytes:
    if canvas is None:
        raise RuntimeError("reportlab not installed")
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    y = 800

    def line(txt, dy=18):
        nonlocal y
        c.drawString(40, y, txt)
        y -= dy

    line(data["name"] or "Candidate", 24)
    contact = " · ".join([x for x in [data["email"], data["phone"], data["location"]] if x])
    if contact:
        line(contact)

    if data["summary"]:
        line("Summary:", 22)
        for chunk in data["summary"].split("\n"):
            line(chunk)

    if data["experience"]:
        line("Experience:", 22)
        for b in data["experience"]:
            line(f"• {b}")

    if data["skills"]:
        line("Skills:", 22)
        line(", ".join(data["skills"]))

    c.showPage()
    c.save()
    return buf.getvalue()


def render():
    _render_header()
    data = _input_section()

    col1, col2 = st.columns(2)
    with col1:
        if st.button("📄 Export DOCX"):
            try:
                content = _export_docx(data)
                st.download_button(
                    "Download CV.docx",
                    data=content,
                    file_name="cv_pro.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as e:
                st.error(f"DOCX export failed: {e}. Install `python-docx` in requirements.txt")

    with col2:
        if st.button("🧾 Export PDF"):
            try:
                content = _export_pdf(data)
                st.download_button(
                    "Download CV.pdf",
                    data=content,
                    file_name="cv_pro.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF export failed: {e}. Install `reportlab` in requirements.txt")

    st.info("Tip: Upload an existing CV in the free CV Builder and use it to prefill here, then polish in Pro.")
