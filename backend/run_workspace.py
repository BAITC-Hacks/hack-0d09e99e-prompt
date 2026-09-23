#!/usr/bin/env python3
"""Build backend/data/workspace.json from a 1C folder using the saved CatBoost model."""

from __future__ import annotations

import json
import os
from pathlib import Path

from qor.pipeline import build_workspace

OUT = Path(os.environ.get("QOR_OUT", Path(__file__).resolve().parent / "data" / "workspace.json"))
DATA_DIR = Path(os.environ.get("IEK_DATA_DIR", "/Users/azamatomirtaj/Documents/IEK"))
SUPPLIER = os.environ.get("QOR_SUPPLIER", "IEK")


def main() -> None:
    bundle = build_workspace(DATA_DIR, SUPPLIER)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(bundle, ensure_ascii=False), encoding="utf-8")
    kpis = bundle["kpis"]
    print(
        f"wrote {OUT}\n"
        f"  sku={kpis['skuTotal']} toOrder={kpis['toOrder']} critical={kpis['critical']}\n"
        f"  asOf={bundle['asOfLabel']} model={bundle['model']['name']}"
    )


if __name__ == "__main__":
    main()
