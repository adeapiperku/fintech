#!/usr/bin/env python3
"""LangChain fraud agent using a local OpenAI-compatible model and RandomForest tool."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

import pandas as pd
from langchain.agents import create_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from sklearn.ensemble import RandomForestClassifier

FEATURE_COLUMNS = [
    "transaction_amount",
    "average_transaction_amount",
    "ip_risk_score",
    "customer_age",
    "previous_failed_logins",
    "transaction_frequency_24h",
    "location_mismatch",
    "device_mismatch",
]


class FraudFeatures(BaseModel):
    transaction_amount: float = Field(..., ge=0)
    average_transaction_amount: float = Field(..., ge=0)
    ip_risk_score: float = Field(..., ge=0, le=100)
    customer_age: float = Field(..., ge=0)
    previous_failed_logins: int = Field(..., ge=0)
    transaction_frequency_24h: int = Field(..., ge=0)
    location_mismatch: int = Field(..., ge=0, le=1)
    device_mismatch: int = Field(..., ge=0, le=1)


class ModelBundle:
    def __init__(self, model: RandomForestClassifier, medians: Dict[str, float]):
        self.model = model
        self.medians = medians


def normalize_base_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return f"{base}/v1" if not base.endswith("/v1") else base


def load_training_data(csv_path: Path) -> Tuple[pd.DataFrame, pd.Series, Dict[str, float]]:
    df = pd.read_csv(csv_path)

    missing_cols = [c for c in FEATURE_COLUMNS + ["fraud_risk_level"] if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in dataset: {missing_cols}")

    X = df[FEATURE_COLUMNS].copy()
    medians = X.median(numeric_only=True).to_dict()
    X = X.fillna(medians)

    # Binary target: anything not Legitimate is treated as fraud-related.
    y = (df["fraud_risk_level"].astype(str).str.strip().str.lower() != "legitimate").astype(int)
    return X, y, medians


def train_random_forest(csv_path: Path, random_state: int) -> ModelBundle:
    X, y, medians = load_training_data(csv_path)
    model = RandomForestClassifier(
        n_estimators=200,
        random_state=random_state,
        n_jobs=-1,
        class_weight="balanced_subsample",
    )
    model.fit(X, y)
    return ModelBundle(model=model, medians=medians)


def build_agent(model_bundle: ModelBundle, llm: ChatOpenAI) -> Any:
    @tool("predict_fraud_with_random_forest", args_schema=FraudFeatures)
    def predict_fraud_with_random_forest(
        transaction_amount: float,
        average_transaction_amount: float,
        ip_risk_score: float,
        customer_age: float,
        previous_failed_logins: int,
        transaction_frequency_24h: int,
        location_mismatch: int,
        device_mismatch: int,
    ) -> str:
        """Predict fraud (fraud/not fraud) from financial record features using RandomForestClassifier."""
        row = {
            "transaction_amount": transaction_amount,
            "average_transaction_amount": average_transaction_amount,
            "ip_risk_score": ip_risk_score,
            "customer_age": customer_age,
            "previous_failed_logins": previous_failed_logins,
            "transaction_frequency_24h": transaction_frequency_24h,
            "location_mismatch": location_mismatch,
            "device_mismatch": device_mismatch,
        }

        x = pd.DataFrame([row], columns=FEATURE_COLUMNS)
        x = x.fillna(model_bundle.medians)

        pred = int(model_bundle.model.predict(x)[0])
        proba = float(model_bundle.model.predict_proba(x)[0][1])

        result = {
            "prediction": "fraud" if pred == 1 else "not_fraud",
            "fraud_probability": round(proba, 4),
            "recommended_action": "review_or_block" if proba >= 0.5 else "approve",
            "features_used": row,
        }
        return json.dumps(result)

    tools = [predict_fraud_with_random_forest]
    system_prompt = (
        "You are a fintech fraud detection agent. "
        "Given a financial report, extract the eight required numerical features and call "
        "the predict_fraud_with_random_forest tool exactly once. "
        "Then return a concise decision summary with the tool output."
    )
    return create_agent(model=llm, tools=tools, system_prompt=system_prompt)


def extract_final_text(agent_output: Any) -> str:
    messages = agent_output.get("messages", []) if isinstance(agent_output, dict) else []
    if not messages:
        return str(agent_output)

    last_message = messages[-1]
    content = getattr(last_message, "content", None)

    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(str(item["text"]))
            else:
                parts.append(str(item))
        return " ".join(parts).strip()

    return str(last_message)


def read_report_text(report_path: Path) -> str:
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    return report_path.read_text(encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LangChain fintech fraud detection agent")
    parser.add_argument(
        "--report",
        required=True,
        help="Path to a text/markdown report describing the financial record(s)",
    )
    parser.add_argument(
        "--dataset",
        default="fintech.csv",
        help="Path to training CSV (default: fintech.csv)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:1234",
        help="Local OpenAI-compatible endpoint (default: http://127.0.0.1:1234)",
    )
    parser.add_argument(
        "--model",
        default="local-model",
        help="Model name exposed by your local endpoint",
    )
    parser.add_argument(
        "--api-key",
        default="lm-studio",
        help="API key value for the local endpoint (placeholder is fine for most local servers)",
    )
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    dataset_path = Path(args.dataset).resolve()
    report_path = Path(args.report).resolve()

    model_bundle = train_random_forest(dataset_path, random_state=args.random_state)

    llm = ChatOpenAI(
        model=args.model,
        base_url=normalize_base_url(args.base_url),
        api_key=args.api_key,
        temperature=0,
    )

    agent_executor = build_agent(model_bundle, llm)
    report_text = read_report_text(report_path)

    user_prompt = (
        "Analyze this financial report and determine if it is fraud or not. "
        "Extract missing values conservatively from context and call the tool.\n\n"
        f"REPORT:\n{report_text}"
    )

    result = agent_executor.invoke({"messages": [{"role": "user", "content": user_prompt}]})
    print("\n=== Agent Final Answer ===")
    print(extract_final_text(result))


if __name__ == "__main__":
    main()
