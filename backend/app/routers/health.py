from fastapi import APIRouter
from pathlib import Path
import os
import subprocess

router = APIRouter()


def _cmd_exists(cmd: str) -> bool:
    try:
        subprocess.run([cmd, "-h"], capture_output=True, check=False)
        return True
    except Exception:
        return False


@router.get("/ocr")
def ocr_health():
    tesseract_cmd = os.environ.get("TESSERACT_CMD")
    poppler_bin = os.environ.get("POPPLER_BIN")

    tesseract_ok = False
    poppler_ok = False

    if tesseract_cmd:
        tesseract_ok = Path(tesseract_cmd).exists()
    else:
        tesseract_ok = _cmd_exists("tesseract")

    if poppler_bin:
        poppler_ok = Path(poppler_bin).exists()
    else:
        poppler_ok = _cmd_exists("pdfinfo")

    return {
        "tesseract_ok": tesseract_ok,
        "poppler_ok": poppler_ok,
        "tesseract_cmd": tesseract_cmd or "tesseract",
        "poppler_bin": poppler_bin or "PATH",
    }
