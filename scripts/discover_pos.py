"""Infer POS schema and transaction aggregates for multiple stores."""
from __future__ import annotations

import json
from pathlib import Path
import pandas as pd

# Apex Retail folder (Docker: /app) or repo parent locally
ROOT = Path(__file__).resolve().parents[2]
OUT_BASE = Path(__file__).resolve().parents[1] / "configs" / "generated"

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


def process_store_1() -> dict:
    store_id = "ST1008"
    out_dir = OUT_BASE / store_id
    out_dir.mkdir(parents=True, exist_ok=True)

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
        "store_id": store_id,
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
    (out_dir / "pos_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    orders.to_csv(out_dir / "pos_transactions_derived.csv", index=False)
    
    # Also write a copy to old generated path for backwards compatibility
    (OUT_BASE / "pos_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    orders.to_csv(OUT_BASE / "pos_transactions_derived.csv", index=False)
    
    return mapping


def process_store_2() -> dict:
    store_id = "ST_STORE2"
    out_dir = OUT_BASE / store_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generate synthetic orders on 2026-03-08 (matching CCTV/sample timeline)
    # We create a dataframe with 5 synthetic transactions
    data = {
        "order_id": ["TXN_ST2_001", "TXN_ST2_002", "TXN_ST2_003", "TXN_ST2_004", "TXN_ST2_005"],
        "store_id": [store_id] * 5,
        "store_name": ["Store_2_Mall"] * 5,
        "timestamp": [
            "2026-03-08 18:11:30",
            "2026-03-08 18:14:15",
            "2026-03-08 18:16:00",
            "2026-03-08 18:18:45",
            "2026-03-08 18:22:10",
        ],
        "nmv": [1450.0, 890.0, 2100.0, 1150.0, 620.0],
        "lines": [2, 1, 3, 2, 1]
    }
    orders = pd.DataFrame(data)
    mapping = {
        "source_file": "synthetic_generator",
        "store_id": store_id,
        "store_name": "Store_2_Mall",
        "city": "Bangalore",
        "date": "08-03-2026",
        "schema": {
            "transaction_key": "order_id",
            "timestamp_columns": ["timestamp"],
            "amount_column": "nmv",
        },
        "stats": {
            "line_items": 9,
            "unique_orders": 5,
            "unique_invoices": 5,
            "time_min": "18:11:30",
            "time_max": "18:22:10",
            "total_nmv_inr": 6210.0,
        },
        "staff_candidates": [
            {"salesperson_id": 901, "employee_code": "EMP_ST2_01", "salesperson_name": "Staff A", "line_count": 5},
            {"salesperson_id": 902, "employee_code": "EMP_ST2_02", "salesperson_name": "Staff B", "line_count": 4}
        ],
        "conversion_window_minutes": 5,
        "confidence": 0.80,
    }
    (out_dir / "pos_mapping.json").write_text(json.dumps(mapping, indent=2), encoding="utf-8")
    orders.to_csv(out_dir / "pos_transactions_derived.csv", index=False)
    return mapping


def main() -> dict:
    OUT_BASE.mkdir(parents=True, exist_ok=True)
    mapping1 = process_store_1()
    mapping2 = process_store_2()
    return {"ST1008": mapping1, "ST_STORE2": mapping2}


if __name__ == "__main__":
    print(json.dumps(main(), indent=2))
