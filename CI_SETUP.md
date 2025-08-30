# CI/CD Setup Guide for Milkbox AI

This document explains how our Continuous Integration (CI) and Repo Health checks are set up.  
It is a record of what we fixed (August 2025) and how to maintain it.

---

## ✅ What Works Now
1. **Smoke Tests** (`smoke.yml`)  
   - Runs a quick import test to check that `streamlit_app` and other modules load.  
   - Confirms nothing is broken before merging.  
   - **Status:** Passing ✅  

2. **Repo Health** (`repo_health.yml`)  
   - Checks for hygiene: LICENSE, README, `__init__.py` files, etc.  
   - Generates a report and uploads as an artifact.  
   - **Status:** Passing ✅  

3. **Repo Steward** (`repo_steward.yml`)  
   - Weekly hygiene run.  
   - Auto-opens/updates issues if warnings are found.  
   - Helps keep the repo self-sufficient.  

---

## 🔒 Branch Protections
- **Main branch** is protected.  
- You cannot push directly to `main`.  
- A Pull Request must pass **Smoke** ✅ and **Repo Health** ✅ before merge.  

---

## 🛠 How to Run Workflows Manually
1. Go to **Actions tab**.  
2. Select **Smoke (Imports)** or **Repo Health**.  
3. Click **Run workflow** (top right).  
4. Choose branch = `main`.  

---

## 📌 Notes
- Python version: **3.11**.  
- Repo is now stable — no more silent breakage.  
- Steward runs every Monday at 04:23 UTC.  

---

## 📅 Next Improvements (optional)
- Add test coverage workflow (pytest).  
- Auto-update dependencies weekly.  
- Add code style check (flake8/black).

---

*Documented by Christo + 007, August 30, 2025.*
