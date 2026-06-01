"""Infer POS schema and transaction aggregates from uploaded CSV."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

# Apex Retail folder (Docker: /app) or repo parent locally
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parents[1] / "configs" / "generated"

REQUIRED_COLUMNS = {"order_id", "order_date", "order_time", "store_id", "NMV"}


def find_pos_csv() -> Path:
    search_dirs = [ROOT, ROOT / "store-intelligence", Path(__file__).resolve().parents[1]]
    candidates: list[Path] = []
    for base in search_dirs:
        if not base.exists():
            continue
        for p in sorted(base.glob("*.csv")):
            name = p.name.lower()
            if "derived" in name or "pos_transactions" in name:
                continue
            if "brigade" in name or "bangalore" in name or "pos" in name:
                candidates.append(p)
    for p in candidates:
        header = pd.read_csv(p, nrows=0).columns
        if REQUIRED_COLUMNS.issubset(set(header)):
            return p
    raise FileNotFoundError(
        f"No Brigade POS CSV with columns {REQUIRED_COLUMNS} under {ROOT}"
    )


def main() -> dict:
    existing = OUT / "pos_mapping.json"
    if existing.exists():
        return json.loads(existing.read_text(encoding="utf-8"))

    csv_path = find_pos_csv()
    df = pd.read_csv(csv_path)
    df["timestamp"] = pd.to_datetime(
        df["order_date"].astype(str) + " " + df["order_time"].astype(str),
        dayfirst=True,
        errors="coerce",
    )
    orders = (
        df.groupby("order_id", as_index=False)
        .agg(
            store_id=("store_id", "first"),
            store_name=("store_name", "first"),
            timestamp=("timestamp", "min"),
            nmv=("NMV", "sum"),
            lines=("sku", "count"),
        )
    )
    staff_ids = (
        df.groupby(["salesperson_id", "employee_code", "salesperson_name"])
        .size()
        .reset_index(name="line_count")
        .sort_values("line_count", ascending=False)
    )
    mapping = {
        "source_file": str(csv_path.name),
        "store_id": str(df["store_id"].iloc[0]),
        "store_name": str(df["store_name"].iloc[0]),
        "city": str(df["city"].iloc[0]),
        "date": str(df["order_date"].iloc[0]),
        "schema": {
            "transaction_key": "order_id",
            "invoice_key": "invoice_number",
            "timestamp_columns": ["order_date", "order_time"],
            "amount_column": "NMV",
            "staff_columns": ["salesperson_id", "employee_code", "salesperson_name"],
        },
        "stats": {
            "line_items": int(len(df)),
            "unique_orders": int(df["order_id"].nunique()),
            "unique_invoices": int(df["invoice_number"].nunique()),
            "time_min": str(df["order_time"].min()),
            "time_max": str(df["order_time"].max()),
            "total_nmv_inr": float(df["NMV"].sum()),
        },
        "staff_candidates": staff_ids.to_dict(orient="records"),
        "conversion_window_minutes": 5,
        "confidence": 0.95,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "pos_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    orders.to_csv(OUT / "pos_transactions_derived.csv", index=False)
    return mapping


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
