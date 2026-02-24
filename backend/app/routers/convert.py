from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from fastapi.responses import FileResponse
from pathlib import Path
from typing import List
from app.services.converter import (
    ensure_workdirs,
    save_upload,
    convert_pdf_to_docx,
    convert_docx_to_pdf,
    convert_pdf_to_text,
    zip_outputs,
    safe_unlink,
)

router = APIRouter()

@router.post("/pdf-to-word")
async def pdf_to_word(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    ensure_workdirs()
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    src_path = await save_upload(file)
    try:
        out_path = convert_pdf_to_docx(src_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    background_tasks.add_task(safe_unlink, src_path)
    background_tasks.add_task(safe_unlink, out_path)

    return FileResponse(
        out_path,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=Path(out_path).name,
    )

@router.post("/word-to-pdf")
async def word_to_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    ensure_workdirs()
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(status_code=400, detail="Only .docx files are supported")

    src_path = await save_upload(file)
    try:
        out_path = convert_docx_to_pdf(src_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    background_tasks.add_task(safe_unlink, src_path)
    background_tasks.add_task(safe_unlink, out_path)

    return FileResponse(
        out_path,
        media_type="application/pdf",
        filename=Path(out_path).name,
    )


@router.post("/pdf-to-text")
async def pdf_to_text(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    ensure_workdirs()
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf files are supported")

    src_path = await save_upload(file)
    try:
        out_path = convert_pdf_to_text(src_path)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    background_tasks.add_task(safe_unlink, src_path)
    background_tasks.add_task(safe_unlink, out_path)

    return FileResponse(
        out_path,
        media_type="text/plain",
        filename=Path(out_path).name,
    )

@router.post("/batch")
async def batch_convert(
    background_tasks: BackgroundTasks,
    target: str = Form(...),
    files: List[UploadFile] = File(...),
):
    ensure_workdirs()
    if target not in {"pdf-to-word", "word-to-pdf", "pdf-to-text"}:
        raise HTTPException(status_code=400, detail="Invalid target")

    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    output_paths = []
    saved_paths = []

    for f in files:
        filename = f.filename.lower()
        if target in {"pdf-to-word", "pdf-to-text"} and not filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="All files must be .pdf")
        if target == "word-to-pdf" and not filename.endswith(".docx"):
            raise HTTPException(status_code=400, detail="All files must be .docx")

        src_path = await save_upload(f)
        saved_paths.append(src_path)

        try:
            if target == "pdf-to-word":
                out_path = convert_pdf_to_docx(src_path)
            elif target == "pdf-to-text":
                out_path = convert_pdf_to_text(src_path)
            else:
                out_path = convert_docx_to_pdf(src_path)
        except RuntimeError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

        output_paths.append(out_path)

    zip_path = zip_outputs(output_paths, target)

    for p in saved_paths + output_paths:
        background_tasks.add_task(safe_unlink, p)

    background_tasks.add_task(safe_unlink, zip_path)

    return FileResponse(
        zip_path,
        media_type="application/zip",
        filename=Path(zip_path).name,
    )
