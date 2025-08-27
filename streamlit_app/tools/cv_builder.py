import io
from datetime import date
from typing import List, Dict, Any

import streamlit as st

# Optional deps for export
try:
    from docx import Document
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.shared import Pt
except Exception:  # pragma: no cover
    Document = None

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:  # pragma: no cover
    canvas = None


# ─────────────────────────────────────────────────────────
# Presets / i18n-lite
# ─────────────────────────────────────────────────────────
COUNTRY_PRESETS = {
    "International": {
        "date_fmt": "%Y-%m",
        "sections": ["Summary", "Experience", "Education", "Skills", "Links"],
        "labels": {"phone": "Phone", "email": "Email", "location": "Location"},
    },
    "United States": {
        "date_fmt": "%b %Y",
        "sections": ["Summary", "Experience", "Education", "Skills", "Links"],
        "labels": {"phone": "Phone", "email": "Email", "location": "Location"},
    },
    "United Kingdom": {
        "date_fmt": "%b %Y",
        "sections": ["Summary", "Experience", "Education", "Skills", "Links"],
        "labels": {"phone": "Tel", "email": "Email", "location": "Location"},
    },
    "Netherlands / Belgium": {
        "date_fmt": "%m-%Y",
        "sections": ["Summary", "Experience", "Education", "Skills", "Links"],
        "labels": {"phone": "Tel", "email": "E-mail", "location": "Locatie"},
    },
    "South Africa": {
        "date_fmt": "%b %Y",
        "sections": ["Summary", "Experience", "Education", "Skills", "Links"],
        "labels": {"phone": "Cell", "email": "Email", "location": "Location"},
    },
}

DEFAULT_COUNTRY = "International"


# ─────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────
def _init_state() -> None:
    ss = st.session_state
    ss.setdefault("cv_personal", {
        "full_name": "",
        "role": "",
        "email": "",
        "phone": "",
        "location": "",
        "website": "",
        "linkedin": "",
        "github": "",
    })
    ss.setdefault("cv_summary", "")
    ss.setdefault("cv_experience", [])        # list of dicts
    ss.setdefault("cv_education", [])         # list of dicts
    ss.setdefault("cv_skills", [])            # list of str
    ss.setdefault("cv_links", [])             # list of dicts
    ss.setdefault("cv_country", DEFAULT_COUNTRY)
    ss.setdefault("cv_template", "Clean")


def _two_cols(label_left: str, label_right: str):
    left, right = st.columns(2)
    with left:
        st.markdown(f"**{label_left}**")
    with right:
        st.markdown(f"**{label_right}**")
    return left, right


def _add_experience_form() -> None:
    st.subheader("Add Experience")
    with st.form("form_exp", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            title = st.text_input("Job title*", key="exp_title")
            start = st.date_input("Start date*", key="exp_start", value=date(2020, 1, 1))
        with c2:
            company = st.text_input("Company*", key="exp_company")
            end = st.date_input("End date (leave if current)", key="exp_end", value=date.today())
            current = st.checkbox("Current role", value=False, key="exp_current")

        desc = st.text_area("Responsibilities / achievements (• one per line)", key="exp_desc", height=120,
                            placeholder="• Shipped X\n• Increased Y by 30%")

        submitted = st.form_submit_button("➕ Add experience")
        if submitted:
            if not title or not company:
                st.warning("Please provide *Job title* and *Company*.")
                return
            bullets = [ln.strip("• ").strip() for ln in desc.splitlines() if ln.strip()]
            st.session_state.cv_experience.append({
                "title": title, "company": company, "start": start, "end": end if not current else None,
                "current": current, "bullets": bullets
            })
            st.success("Experience added.")


def _add_education_form() -> None:
    st.subheader("Add Education")
    with st.form("form_edu", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            degree = st.text_input("Degree / Program*", key="edu_degree")
            start = st.date_input("Start date*", key="edu_start", value=date(2018, 1, 1))
        with c2:
            institution = st.text_input("Institution*", key="edu_institution")
            end = st.date_input("End date*", key="edu_end", value=date(2022, 1, 1))
        notes = st.text_input("Notes (e.g., honors, GPA)", key="edu_notes")

        submitted = st.form_submit_button("➕ Add education")
        if submitted:
            if not degree or not institution:
                st.warning("Please provide *Degree* and *Institution*.")
                return
            st.session_state.cv_education.append({
                "degree": degree, "institution": institution, "start": start, "end": end, "notes": notes
            })
            st.success("Education added.")


def _add_skill_form() -> None:
    st.subheader("Add Skill")
    with st.form("form_skill", clear_on_submit=True):
        skill = st.text_input("Skill (e.g., Python, Leadership)*", key="skill_val")
        submitted = st.form_submit_button("➕ Add skill")
        if submitted:
            if not skill.strip():
                st.warning("Please enter a skill.")
                return
            st.session_state.cv_skills.append(skill.strip())
            st.success("Skill added.")


def _add_link_form() -> None:
    st.subheader("Add Link")
    with st.form("form_link", clear_on_submit=True):
        label = st.text_input("Label (e.g., Portfolio, Kaggle)", key="link_label")
        url = st.text_input("URL", key="link_url")
        submitted = st.form_submit_button("➕ Add link")
        if submitted:
            if not label or not url:
                st.warning("Please provide *Label* and *URL*.")
                return
            st.session_state.cv_links.append({"label": label, "url": url})
            st.success("Link added.")


def _format_date(d: date, fmt: str) -> str:
    try:
        return d.strftime(fmt)
    except Exception:
        return str(d)


def _docx_header(doc, text: str, size=18, bold=True):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    return p


def build_docx(cv: Dict[str, Any]) -> bytes:
    """Create a .docx CV and return raw bytes."""
    if Document is None:
        raise RuntimeError("python-docx not available")

    doc = Document()

    # Header
    full_name = cv["personal"]["full_name"].strip() or "Your Name"
    role = cv["personal"]["role"].strip()
    name_p = _docx_header(doc, full_name, size=22)
    if role:
        p_role = doc.add_paragraph()
        run = p_role.add_run(role)
        run.italic = True
        run.font.size = Pt(12)

    # Contact line
    labels = cv["labels"]
    contact_bits = []
    for k in ("email", "phone", "location", "website", "linkedin", "github"):
        val = cv["personal"].get(k) or ""
        if val:
            label = labels.get(k, k.capitalize())
            contact_bits.append(f"{label}: {val}")
    if contact_bits:
        p = doc.add_paragraph(" | ".join(contact_bits))
        p.runs[0].font.size = Pt(9)

    # Summary
    if cv["summary"].strip():
        _docx_header(doc, "Summary", size=14)
        doc.add_paragraph(cv["summary"].strip())

    # Experience
    if cv["experience"]:
        _docx_header(doc, "Experience", size=14)
        for item in cv["experience"]:
            title = item["title"]; company = item["company"]
            start = _format_date(item["start"], cv["date_fmt"])
            end = "Present" if item["current"] else _format_date(item["end"], cv["date_fmt"])
            doc.add_paragraph(f"{title} — {company}  ({start} – {end})")
            for b in item["bullets"]:
                doc.add_paragraph(b, style="List Bullet")

    # Education
    if cv["education"]:
        _docx_header(doc, "Education", size=14)
        for ed in cv["education"]:
            start = _format_date(ed["start"], cv["date_fmt"])
            end = _format_date(ed["end"], cv["date_fmt"])
            line = f"{ed['degree']} — {ed['institution']} ({start} – {end})"
            if ed.get("notes"):
                line += f" — {ed['notes']}"
            doc.add_paragraph(line)

    # Skills
    if cv["skills"]:
        _docx_header(doc, "Skills", size=14)
        doc.add_paragraph(", ".join(cv["skills"]))

    # Links
    if cv["links"]:
        _docx_header(doc, "Links", size=14)
        for link in cv["links"]:
            doc.add_paragraph(f"{link['label']}: {link['url']}")

    bio = io.BytesIO()
    doc.save(bio)
    return bio.getvalue()


def build_pdf(cv: Dict[str, Any]) -> bytes:
    """Simple text PDF (fallback)."""
    if canvas is None:
        raise RuntimeError("reportlab not available")

    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4

    y = height - 50
    def line(txt: str, sz=10, gap=14, bold=False):
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", sz)
        c.drawString(40, y, txt)
        y -= gap

    # Header
    full_name = cv["personal"]["full_name"].strip() or "Your Name"
    role = cv["personal"]["role"].strip()
    line(full_name, sz=16, gap=20, bold=True)
    if role:
        line(role, sz=11, gap=16)

    # Contact
    contact_bits = []
    labels = cv["labels"]
    for k in ("email", "phone", "location", "website", "linkedin", "github"):
        val = cv["personal"].get(k) or ""
        if val:
            contact_bits.append(f"{labels.get(k, k.capitalize())}: {val}")
    if contact_bits:
        line(" | ".join(contact_bits), sz=8, gap=16)

    # Sections
    if cv["summary"].strip():
        line("Summary", sz=12, gap=16, bold=True)
        for para in cv["summary"].splitlines():
            line(para, sz=10, gap=14)

    if cv["experience"]:
        line("Experience", sz=12, gap=16, bold=True)
        for it in cv["experience"]:
            start = _format_date(it["start"], cv["date_fmt"])
            end = "Present" if it["current"] else _format_date(it["end"], cv["date_fmt"])
            line(f"{it['title']} — {it['company']} ({start} – {end})", sz=10, gap=14)
            for b in it["bullets"]:
                line(f"• {b}", sz=10, gap=14)

    if cv["education"]:
        line("Education", sz=12, gap=16, bold=True)
        for ed in cv["education"]:
            start = _format_date(ed["start"], cv["date_fmt"])
            end = _format_date(ed["end"], cv["date_fmt"])
            t = f"{ed['degree']} — {ed['institution']} ({start} – {end})"
            if ed.get("notes"):
                t += f" — {ed['notes']}"
            line(t, sz=10, gap=14)

    if cv["skills"]:
        line("Skills", sz=12, gap=16, bold=True)
        line(", ".join(cv["skills"]), sz=10, gap=16)

    if cv["links"]:
        line("Links", sz=12, gap=16, bold=True)
        for link in cv["links"]:
            line(f"{link['label']}: {link['url']}", sz=10, gap=14)

    c.showPage()
    c.save()
    return bio.getvalue()


def _build_cv_dict() -> Dict[str, Any]:
    preset = COUNTRY_PRESETS.get(st.session_state.cv_country, COUNTRY_PRESETS[DEFAULT_COUNTRY])
    return {
        "personal": st.session_state.cv_personal,
        "summary": st.session_state.cv_summary or "",
        "experience": st.session_state.cv_experience,
        "education": st.session_state.cv_education,
        "skills": st.session_state.cv_skills,
        "links": st.session_state.cv_links,
        "date_fmt": preset["date_fmt"],
        "labels": {**{k: k.capitalize() for k in ("phone", "email", "location")}, **preset["labels"]},
    }


# ─────────────────────────────────────────────────────────
# Streamlit UI
# ─────────────────────────────────────────────────────────
def render():
    st.header("📄 International CV Builder")

    _init_state()

    # Sidebar config
    st.sidebar.subheader("Settings")
    st.session_state.cv_country = st.sidebar.selectbox(
        "Country / Locale", list(COUNTRY_PRESETS.keys()), index=list(COUNTRY_PRESETS.keys()).index(DEFAULT_COUNTRY)
    )
    st.session_state.cv_template = st.sidebar.selectbox("Template", ["Clean", "Compact"])

    st.sidebar.caption("Your progress is kept in session only (clears on refresh).")

    # Personal info
    st.subheader("Personal information")
    p = st.session_state.cv_personal
    c1, c2 = st.columns(2)
    with c1:
        p["full_name"] = st.text_input("Full name*", value=p["full_name"])
        p["email"] = st.text_input("Email", value=p["email"])
        p["website"] = st.text_input("Website / Portfolio", value=p["website"])
        p["linkedin"] = st.text_input("LinkedIn", value=p["linkedin"])
    with c2:
        p["role"] = st.text_input("Target role / Headline", value=p["role"])
        p["phone"] = st.text_input(COUNTRY_PRESETS[st.session_state.cv_country]["labels"]["phone"], value=p["phone"])
        p["location"] = st.text_input(COUNTRY_PRESETS[st.session_state.cv_country]["labels"]["location"], value=p["location"])
        p["github"] = st.text_input("GitHub", value=p["github"])

    # Summary
    st.subheader("Professional summary")
    st.session_state.cv_summary = st.text_area(
        "Brief paragraph about yourself (3-5 lines)",
        value=st.session_state.cv_summary,
        height=120,
        placeholder="Product-minded software engineer with 7+ years..."
    )

    # Experience / Education / Skills / Links
    st.divider()
    _add_experience_form()
    if st.session_state.cv_experience:
        st.write("**Experience entries**")
        for i, item in enumerate(st.session_state.cv_experience):
            with st.expander(f"{item['title']} — {item['company']}"):
                st.write(f"**Dates:** {_format_date(item['start'], _build_cv_dict()['date_fmt'])} – "
                         f"{'Present' if item['current'] else _format_date(item['end'], _build_cv_dict()['date_fmt'])}")
                for b in item["bullets"]:
                    st.write(f"- {b}")
                if st.button(f"Remove", key=f"rm_exp_{i}"):
                    st.session_state.cv_experience.pop(i)
                    st.experimental_rerun()

    st.divider()
    _add_education_form()
    if st.session_state.cv_education:
        st.write("**Education entries**")
        for i, ed in enumerate(st.session_state.cv_education):
            with st.expander(f"{ed['degree']} — {ed['institution']}"):
                st.write(f"{_format_date(ed['start'], _build_cv_dict()['date_fmt'])} – {_format_date(ed['end'], _build_cv_dict()['date_fmt'])}")
                if ed.get("notes"):
                    st.write(ed["notes"])
                if st.button("Remove", key=f"rm_edu_{i}"):
                    st.session_state.cv_education.pop(i)
                    st.experimental_rerun()

    st.divider()
    _add_skill_form()
    if st.session_state.cv_skills:
        st.write("**Skills**")
        cols = st.columns(6)
        for i, sk in enumerate(st.session_state.cv_skills):
            cols[i % 6].markdown(f"- {sk}")
        if st.button("Clear all skills"):
            st.session_state.cv_skills.clear()
            st.success("Skills cleared.")

    st.divider()
    _add_link_form()
    if st.session_state.cv_links:
        st.write("**Links**")
        for i, l in enumerate(st.session_state.cv_links):
            st.write(f"- [{l['label']}]({l['url']})")
        if st.button("Clear links"):
            st.session_state.cv_links.clear()

    # Preview & Export
    st.divider()
    st.subheader("Preview & Export")
    cv = _build_cv_dict()

    c1, c2 = st.columns(2)
    with c1:
        if Document:
            try:
                docx_bytes = build_docx(cv)
                st.download_button(
                    "⬇️ Download DOCX",
                    data=docx_bytes,
                    file_name=f"{cv['personal']['full_name'] or 'CV'}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )
            except Exception as e:
                st.error(f"DOCX export error: {e}")
        else:
            st.info("DOCX export unavailable (python-docx not installed).")

    with c2:
        if canvas:
            try:
                pdf_bytes = build_pdf(cv)
                st.download_button(
                    "⬇️ Download PDF (simple)",
                    data=pdf_bytes,
                    file_name=f"{cv['personal']['full_name'] or 'CV'}.pdf",
                    mime="application/pdf",
                )
            except Exception as e:
                st.error(f"PDF export error: {e}")
        else:
            st.info("PDF export unavailable (reportlab not installed).")

    st.caption("Tip: Use concise bullets (impact + numbers), tailor to job, keep to 1–2 pages.")
