"""CatBoost service: turns a 1C folder into the workspace JSON.

The order API does not load the model. It calls POST /build here.
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile

from qor.contract import MODEL_NAME
from qor.pipeline import MODEL_PATH, build_workspace

app = FastAPI(title="Qor ML", version="0.2.0")


@app.get("/health")
def health() -> dict:
    return {"ok": True, "model": MODEL_NAME, "ready": MODEL_PATH.exists()}


@app.post("/build")
async def build(
    files: list[UploadFile] | None = File(None),
    supplier: str = "IEK",
    demo: bool = False,
) -> dict:
    if demo:
        folder = Path(os.environ.get("IEK_DATA_DIR", "/data/iek"))
    else:
        uploads = [item for item in (files or []) if item.filename]
        if not uploads:
            raise HTTPException(status_code=400, detail="Загрузите выгрузки 1С (xlsx)")
        tmp = tempfile.TemporaryDirectory()
        folder = Path(tmp.name)
        for upload in uploads:
            name = Path(upload.filename or "upload.xlsx").name
            (folder / name).write_bytes(await upload.read())
        try:
            return build_workspace(folder, supplier)
        except FileNotFoundError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        finally:
            tmp.cleanup()

    try:
        return build_workspace(folder, supplier)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
