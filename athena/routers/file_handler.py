import os
import re
import io
import logging
import time

from pypdf import PdfReader, PdfWriter
from athena.libs.indexer import CognitiveIndex
from fastapi import APIRouter, UploadFile, Request

router = APIRouter(tags=["file"], prefix="/file")
logger = logging.getLogger()


def blob_name_from_file_page(filename, page=0):
    if os.path.splitext(filename)[1].lower() == ".pdf":
        return os.path.splitext(os.path.basename(filename))[0] + f"-{page}" + ".pdf"
    else:
        return os.path.basename(filename)


@router.post("/upload")
async def upload(request: Request, uploaded_file: UploadFile, category: str = None):
    blob_container = request.app.state.blob_container
    try:
        if uploaded_file.content_type == "application/pdf":
            reader = PdfReader(uploaded_file.file)
            pages = reader.pages
            for i in range(len(pages)):
                blob_name = blob_name_from_file_page(uploaded_file.filename, i)
                f = io.BytesIO()
                writer = PdfWriter()
                writer.add_page(pages[i])
                writer.write(f)
                f.seek(0)
                blob_container.upload_blob(blob_name, f, overwrite=True)
        else:
            blob_name = blob_name_from_file_page(uploaded_file.filename)
            data = uploaded_file.file.read()
            blob_container.upload_blob(blob_name, data, overwrite=True)
    except Exception:
        raise Exception("Error in uploading to Azure Blob Storage")

    try:
        uploaded_file.file.seek(0, 0)
        data = uploaded_file.file.read()
        CognitiveIndex(
            filename=uploaded_file.filename,
            file_data=data,
            formrecognizer=request.app.state.formrecognizer,
            cognitive_search=request.app.state.cognitive_search,
            category=category,
        )
    except Exception:
        raise Exception("Cognitive indexer error")

    return {"Uploaded": uploaded_file.filename}


# TODO: Handle paged blobs being listed separately
@router.get("/list")
async def get_files(request: Request):
    blob_container = request.app.state.blob_container
    blob_iter = blob_container.list_blob_names()
    blob_list = []
    blob = blob_iter.next()
    while blob:
        blob_list.append(blob)
        try:
            blob = blob_iter.next()
        except:
            blob = False

    return {"files": blob_list}


@router.post("/remove")
async def remove(request: Request, filename: str = None):
    blob_container = request.app.state.blob_container
    search_client = request.app.state.cognitive_search
    if filename == None:
        blobs = blob_container.list_blob_names()
    else:
        prefix = os.path.splitext(os.path.basename(filename))[0]
        blobs = filter(
            lambda b: re.match(f"{prefix}-\d+\.*", b),
            blob_container.list_blob_names(
                name_starts_with=os.path.splitext(os.path.basename(prefix))[0]
            ),
        )
    for blob in blobs:
        logger.info(f"Removing blob {blob}...")
        blob_container.delete_blob(blob)
    while True:
        filter = (
            None
            if filename == None
            else f"sourcefile eq '{os.path.basename(filename)}'"
        )
        r = search_client.search("", filter=filter, top=1000, include_total_count=True)
        if r.get_count() == 0:
            break
        r = search_client.delete_documents(documents=[{"id": d["id"]} for d in r])
        time.sleep(2)
