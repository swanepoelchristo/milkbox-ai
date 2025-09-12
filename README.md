# Milkbox AI

## CI Status Panel  

[![Smoke (Imports)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/smoke.yml/badge.svg)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/smoke.yml)
[![Repo Health](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_health.yml/badge.svg)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_health.yml)
[![Repo Doctor](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_doctor.yml/badge.svg)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_doctor.yml)
[![Repo Steward](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_steward.yml/badge.svg)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/repo_steward.yml)
[![CodeQL](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/codeql.yml/badge.svg)](https://github.com/swanepoelchristo/milkbox-ai/actions/workflows/codeql.yml)

---

Milkbox AI repository with CI protection:

- **Smoke (Imports):** ensures all Python modules import cleanly  
- **Repo Health:** checks repo hygiene, dependencies, and reports issues  
- **Repo Doctor:** enforces repo standards and templates  
- **Repo Steward:** keeps automation + governance in check  
- **CodeQL:** scans for security vulnerabilities  

---

# Milkbox AI  

Prototype Streamlit app for Milkbox AI.  

## Run locally  

```bash
pip install -r streamlit_app/requirements.txt  
streamlit run streamlit_app/app.py 
