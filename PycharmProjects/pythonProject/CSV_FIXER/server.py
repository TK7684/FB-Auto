import os
import shutil
import time
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from csv_fixer_core.fixers import (
    process_csv_file,
    process_csv_pandas,
    fix_header_only,
    get_platform_headers
)
from csv_fixer_core.utils import ensure_directory_exists, get_output_filename

app = FastAPI(title="CSV Fixer Pro API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify the actual domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
ensure_directory_exists(UPLOAD_DIR)
ensure_directory_exists(OUTPUT_DIR)

class ProcessResponse(BaseModel):
    job_id: str
    status: str
    filename: str
    output_url: str
    fixes: List[str]
    row_count: int
    processing_time: float

@app.get("/")
async def root():
    return {"message": "CSV Fixer Pro API is running"}

@app.post("/fix", response_model=ProcessResponse)
async def fix_csv(
    file: UploadFile = File(...),
    column_names: bool = Form(True),
    timestamps: bool = Form(True),
    column_count: bool = Form(False),
    encoding: bool = Form(True),
    newlines: bool = Form(True),
    quotes: bool = Form(True),
    separators: bool = Form(True),
    platform: Optional[str] = Form(None),
    use_fast_mode: bool = Form(True)
):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    
    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    output_filename = get_output_filename(file.filename, OUTPUT_DIR, f"_{platform or 'standard'}_fixed")
    
    options = {
        "column_names": column_names,
        "timestamps": timestamps,
        "column_count": column_count,
        "encoding": encoding,
        "newlines": newlines,
        "quotes": quotes,
        "separators": separators
    }
    
    start_time = time.time()
    
    try:
        if use_fast_mode:
            fixes, row_count = process_csv_pandas(input_path, output_filename, options, platform=platform)
            if fixes and fixes[0].startswith("Error: Pandas not installed"):
                fixes, row_count = process_csv_file(input_path, output_filename, options, platform=platform)
        else:
            fixes, row_count = process_csv_file(input_path, output_filename, options, platform=platform)
            
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            job_id=job_id,
            status="completed",
            filename=os.path.basename(output_filename),
            output_url=f"/download/{os.path.basename(output_filename)}",
            fixes=fixes,
            row_count=row_count,
            processing_time=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fast-fix", response_model=ProcessResponse)
async def fast_fix_csv(
    file: UploadFile = File(...),
    platform: str = Form(...),
    repair_rows: bool = Form(True)
):
    job_id = str(uuid.uuid4())
    input_path = os.path.join(UPLOAD_DIR, f"{job_id}_{file.filename}")
    
    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    output_filename = get_output_filename(file.filename, OUTPUT_DIR, f"_{platform}_fast_fixed")
    
    start_time = time.time()
    
    try:
        fixes, row_count = fix_header_only(input_path, output_filename, platform, repair_rows=repair_rows)
        processing_time = time.time() - start_time
        
        return ProcessResponse(
            job_id=job_id,
            status="completed",
            filename=os.path.basename(output_filename),
            output_url=f"/download/{os.path.basename(output_filename)}",
            fixes=fixes,
            row_count=row_count,
            processing_time=round(processing_time, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
