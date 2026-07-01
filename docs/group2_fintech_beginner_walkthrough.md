# 💳 Group 2 — FinTech Fraud — Beginner Walkthrough & Challenge

This guide assumes you've never done a data project before. **Copy each code block into a
Jupyter notebook cell and run it in order.** After every step there's a ✅ checkpoint.

**What you're building:** a system that looks at bank transactions, decides how likely each
one is to be fraud, estimates how much money could be lost, and lets an AI assistant explain suspicious activity and say whether to approve, review, or block a transaction.

**Your file:** `fintech.csv` (about 100,800 rows).

---

## STEP 0 — Get set up
```python
!pip install pandas numpy matplotlib seaborn
```
```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
```

---

## 🎯 STEP 1 — Open the data and look at it
```python
df = pd.read_csv("fintech.csv")
print("Rows, Columns:", df.shape)
df.head()
```
```python
df.isna().sum()        # empty cells per column
df.duplicated().sum()  # exact-copy rows
```

✅ **You beat Step 1 when:** you can see the table and notice some empty cells plus ~800
duplicate rows. The mess is intentional — you'll clean it next.

---

## 🧹 STEP 2 — Clean the data
```python
# 1) Remove duplicate rows
df = df.drop_duplicates()

# 2) A customer age of -1 is impossible. Turn it into "empty".
df.loc[df["customer_age"] == -1, "customer_age"] = np.nan

# 3) The transaction_type column has messy casing (Transfer, TRANSFER).
#    Make everything lowercase so they match.
df["transaction_type"] = df["transaction_type"].astype(str).str.strip().str.lower()

# 4) Turn the date text into real dates.
df["transaction_date"] = pd.to_datetime(df["transaction_date"], format="mixed",
                                        dayfirst=True, errors="coerce")

# 5) Fill empty number cells with each column's median (middle value).
for col in ["ip_risk_score", "customer_age", "average_transaction_amount"]:
    df[col] = df[col].fillna(df[col].median())

print("Empty cells left:", df.isna().sum().sum())
print("Transaction types:", df["transaction_type"].unique())
```

✅ **You beat Step 2 when:** "Empty cells left" is 0 and the transaction types are all clean
lowercase words.

---

## 🔍 STEP 3 — Explore the data (make charts)
Make these and write one sentence under each saying what it means.
```python
# Chart 1: how many transactions fall into each risk level
df["fraud_risk_level"].value_counts().plot(kind="bar", title="Transactions by risk level")
plt.show()

# Chart 2: which merchant types have the most fraud
df.groupby("merchant_category")["fraud_risk_level"].value_counts().unstack().plot(
    kind="bar", stacked=True, title="Risk by merchant category")
plt.show()

# Chart 3: how transaction amounts are spread
df["transaction_amount"].plot(kind="hist", bins=50, title="Transaction amount spread")
plt.show()
```
Example sentence: *"Most transactions are Legitimate, but gambling and crypto merchants have
the highest share of Fraudulent ones."*

✅ **You beat Step 3 when:** you have 4–5 charts, each with a written takeaway, including one
"which category is riskiest" chart.

---

## ⚔️ STEP 4 — Classification (decide each transaction's risk)

**Classification = sorting into named groups:** Legitimate / Suspicious / High Risk /
Fraudulent. Unlike some datasets, the fraud "score" isn't already in the file, so we build it
from the clues, then turn it into a label.

```python
# How big is this payment compared to the customer's usual? (a key fraud clue)
ratio = (df["transaction_amount"] / df["average_transaction_amount"].clip(lower=1)).clip(0, 10)

# Add up the warning signs into a fraud score
score = (ratio * 6
         + df["ip_risk_score"] * 0.3
         + df["location_mismatch"] * 18      # paying from an unexpected place
         + df["device_mismatch"] * 16        # paying from an unexpected device
         + df["previous_failed_logins"] * 5
         + (df["transaction_frequency_24h"] > 8) * 12   # many payments in a day
         + df["merchant_category"].isin(["gambling", "crypto"]) * 10)

# Turn the score into a risk label
df["my_risk"] = pd.cut(score, bins=[-1, 35, 60, 80, 200],
    labels=["Legitimate", "Suspicious", "High Risk", "Fraudulent"])
```

Check how well your rule matches the official answer:
```python
agreement = (df["my_risk"].astype(str) == df["fraud_risk_level"].astype(str)).mean()
print(f"My rule matches the answer key {agreement:.0%} of the time")
```

✅ **You beat Step 4 when:** the match is **about 85% or higher**. It's not 100% on purpose —
real data has noise, and the ~15% gap is your chance to explain *why* rules aren't perfect.
That explanation earns marks.

---

## 🔮 STEP 5 — Regression (estimate the possible loss)

**Regression = predicting a number.** Here: how much money could be lost on a transaction.
Riskier transactions risk a bigger share of the amount.

```python
loss_share = df["fraud_risk_level"].map({
    "Legitimate": 0.0, "Suspicious": 0.15, "High Risk": 0.5, "Fraudulent": 0.95})
df["my_loss"] = df["transaction_amount"] * loss_share
```

Check closeness to the real loss column:
```python
print("Closeness (1.0 = perfect):", round(df["my_loss"].corr(df["estimated_fraud_loss"]), 2))
```

✅ **You beat Step 5 when:** the closeness is **above 0.9**.

**Save your cleaned data for the agent:**
```python
df.to_csv("fintech_cleaned.csv", index=False)
```

---

## 🤖 STEP 6 — Build the AI agent

**What is an AI agent?** A chatbot you give (a) instructions and (b) your data file, so it can
answer questions about the data. Build Stage A first (it already passes), then Stage B for
extra marks.

### Stage A — one simple agent (start here)
In **Azure AI Foundry**:
1. Create a project and deploy a chat model.
2. Create an **Agent** and upload `fintech_cleaned.csv` as a **knowledge / file**.
3. Turn on **Code Interpreter** (needed for totals like "total fraud exposure").
4. Paste these instructions:
```
You are a Fraud Risk Analyst for a digital bank. You help investigators decide whether
to approve, review, or block transactions.

For every answer, use these 5 steps:
1. What happened — the key clues (amount vs the customer's average, location/device
   mismatch, IP risk).
2. Why it matters — the fraud pattern those clues form.
3. Risk level — Legitimate / Suspicious / High Risk / Fraudulent, and the rule that decided it.
4. Estimate — possible money lost (in euros) and how you got it.
5. Action — Approve / Review / Hold for review / Block.

Always mention the actual numbers. For "total exposure" questions, add up the loss column.
Never invent missing values — say if something is missing.
```
5. Test with: *"What is the total estimated fraud exposure?"*

### Stage B — multiple agents (the upgrade)
A multi-agent system is **one boss agent that asks helper agents**:

| Agent | Its one job |
|-------|-------------|
| **Transaction Classifier** | apply the Step 4 rules and give the risk level + why |
| **Loss Estimator** | apply the Step 5 formula (one transaction or a total) |
| **Investigation Reporter** | summarise fraud trends by merchant, country, or customer |
| **Fraud Analyst (boss)** | takes the question, asks the right helper, writes the 5-step answer |

> **Beginner tip:** instead of three separate agents, you can make **one agent with three
> tools** doing these jobs. That still counts as multi-agent and is much easier.

✅ **You beat Step 6 when:** you ask *"Why was [pick a Fraudulent transaction] flagged?"* and
the agent gives all 5 steps, real numbers, and an approve/block/review decision.

---

## 🎮 STEP 7 — Make a simple prototype (the demo)
```python
def ask(question):
    # send `question` to your Foundry agent and print its reply
    ...
ask("Should transaction TX00091245 be approved, blocked, or reviewed?")
```
Simple and reliable beats fancy and broken. **Record a backup video.**

✅ **You beat Step 7 — and the whole challenge — when:** a teammate types a question and gets
a correct, fully-explained answer with an approve/block/review call, live.

---

## 🏁 Quick checklist before you submit
- [ ] Cleaned data: no duplicates, no -1 ages, tidy transaction types, real dates, no empty cells
- [ ] 4–5 charts, each with a written insight
- [ ] Classification rule (~85%+ match) and loss formula (closeness > 0.9)
- [ ] An agent in Foundry answering the 6 example questions with the 5-step reasoning
- [ ] A working demo + a backup video
- [ ] Architecture diagram, 2–4 page report, 15-minute presentation where everyone speaks
