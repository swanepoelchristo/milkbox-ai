# Milkbox AI

[![Repo Doctor](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_doctor.yml/badge.svg)](../../actions/workflows/repo_doctor.yml)
[![Smoke](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/smoke.yml/badge.svg)](../../actions/workflows/smoke.yml)
[![Repo Health](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/health.yml/badge.svg)](../../actions/workflows/health.yml)

Milkbox AI repository with CI protection:
- **Repo Doctor:** validates repo structure, required files, and Python setup  
- **Smoke (Imports):** ensures all Python modules import cleanly  
- **Repo Health:** checks repo hygiene, dependencies, and reports issues  

---

# Milkbox AI  

Prototype Streamlit app for Milkbox AI.  

## Tools
- **War Room** → [`streamlit_app/tools/war_room.py`](streamlit_app/tools/war_room.py)  
  A dashboard for monitoring, coordination, and quick response during active development.  

---

## Run locally
```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
