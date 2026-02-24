from pathlib import Path
from uuid import uuid4
import shutil
import zipfile
from fastapi import UploadFile
import os

BASE_DIR = Path(__file__).resolve().parents[1]
TEMP_DIR = BASE_DIR / "temp"
UPLOAD_DIR = TEMP_DIR / "uploads"
OUTPUT_DIR = TEMP_DIR / "outputs"
ZIP_DIR = TEMP_DIR / "zips"


def ensure_workdirs():
    for d in [TEMP_DIR, UPLOAD_DIR, OUTPUT_DIR, ZIP_DIR]:
        d.mkdir(parents=True, exist_ok=True)


async def save_upload(file: UploadFile) -> Path:
    suffix = Path(file.filename).suffix
    target = UPLOAD_DIR / f"{uuid4().hex}{suffix}"
    with target.open("wb") as f:
        content = await file.read()
        f.write(content)
    return target


def convert_pdf_to_docx(src_path: Path) -> Path:
    try:
        from pdf2docx import Converter
    except Exception as exc:
        raise RuntimeError(
            "PDF → Word dependencies missing. Install requirements-heavy.txt."
        ) from exc
    out_path = OUTPUT_DIR / f"{src_path.stem}.docx"
    cv = Converter(str(src_path))
    cv.convert(str(out_path), start=0, end=None)
    cv.close()
    return out_path


def convert_docx_to_pdf(src_path: Path) -> Path:
    try:
        from docx2pdf import convert
    except Exception as exc:
        raise RuntimeError(
            "Word → PDF dependencies missing. Install requirements-heavy.txt."
        ) from exc
    out_path = OUTPUT_DIR / f"{src_path.stem}.pdf"
    convert(str(src_path), str(out_path))
    return out_path


def convert_pdf_to_text(src_path: Path) -> Path:
    try:
        from pdf2image import convert_from_path
        import pytesseract
    except Exception as exc:
        raise RuntimeError(
            "OCR dependencies missing. Install requirements-ocr.txt."
        ) from exc

    tesseract_cmd = os.environ.get("TESSERACT_CMD")
    if tesseract_cmd:
        pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

    poppler_bin = os.environ.get("POPPLER_BIN")
    pages = convert_from_path(str(src_path), dpi=200, poppler_path=poppler_bin)
    text_parts = []
    for i, page in enumerate(pages, start=1):
        text = pytesseract.image_to_string(page)
        text_parts.append(f"\n\n--- Page {i} ---\n\n{text}".strip())

    out_path = OUTPUT_DIR / f"{src_path.stem}.txt"
    out_path.write_text("\n".join(text_parts), encoding="utf-8")
    return out_path


def extract_pdf_text(src_path: Path, max_chars: int = 12000) -> str:
    text = ""

    try:
        import fitz  # PyMuPDF

        doc = fitz.open(str(src_path))
        parts = []
        for page in doc:
            parts.append(page.get_text())
        doc.close()
        text = "\n".join(parts).strip()
    except Exception:
        text = ""

    if not text:
        try:
            from pdf2image import convert_from_path
            import pytesseract
        except Exception as exc:
            raise RuntimeError(
                "PDF text extraction requires PyMuPDF or OCR deps. Install requirements-heavy.txt or requirements-ocr.txt."
            ) from exc

        tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd

        poppler_bin = os.environ.get("POPPLER_BIN")
        pages = convert_from_path(str(src_path), dpi=200, poppler_path=poppler_bin)
        ocr_parts = []
        for page in pages:
            ocr_parts.append(pytesseract.image_to_string(page))
        text = "\n".join(ocr_parts).strip()

    if len(text) > max_chars:
        text = text[:max_chars] + "\n\n[Truncated]"

    return text


def zip_outputs(paths, target_label: str) -> Path:
    zip_path = ZIP_DIR / f"batch_{target_label}_{uuid4().hex}.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in paths:
            zf.write(p, arcname=Path(p).name)
    return zip_path


def safe_unlink(path: Path):
    try:
        Path(path).unlink(missing_ok=True)
    except Exception:
        pass
