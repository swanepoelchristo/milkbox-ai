# Milkbox AI

[![Repo Doctor](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_doctor.yml/badge.svg)](../../actions/workflows/repo_doctor.yml)
[![Smoke](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/smoke.yml/badge.svg)](../../actions/workflows/smoke.yml)
[![Repo Health](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/health.yml/badge.svg)](../../actions/workflows/health.yml)

Milkbox AI repository with CI protection:
- **Repo Doctor:** validates repo structure, required files, and Python setup  
- **Smoke (Imports):** ensures all Python modules import cleanly  
- **Repo Health:** checks repo hygiene, dependencies, and reports issues  

---

## Overview

Prototype Streamlit app for Milkbox AI.

## Tools

- **War Room** → [`streamlit_app/tools/war_room.py`](streamlit_app/tools/war_room.py)  
  CI dashboard showing the status of **Repo Doctor**, **Smoke**, and **Repo Health**.  
  - Uses GitHub API when `GITHUB_TOKEN` is set; otherwise falls back to public badges.  
  - Exposes `render()` for the tools loader and can run standalone.

---

## Run locally

```bash
pip install -r requirements.txt
streamlit run streamlit_app/app.py
