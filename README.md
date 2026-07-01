# 💳 FinTech Fraud Detection Project

This project analyzes financial transactions to detect fraudulent activity using data preprocessing, machine learning logic, and an AI-powered fraud investigation agent.

---

## 📦 Project Setup

### 1. Create a Virtual Environment (Python 3.10)

Make sure Python 3.10 is installed, then run:

```bash
py -3.10 -m venv .venv
pip install -r requirements.txt

# Activate Virtual Environment
# Windows (CMD / PowerShell)
.venv\Scripts\activate
# Mac / Linux
source .venv/bin/activate

## 🧼 Notebook Output Handling (Important for Git)

To avoid committing Jupyter notebook outputs (which can make the repo messy), we use automatic cleanup tools.

### Option 1 — Install nbstripout (Recommended)

```bash
pip install nbstripout
nbstripout --install #(enable the library)