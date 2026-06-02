from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, Query, Request
from sqlalchemy.orm import Session
from typing import Optional

from database.connection.database import get_db
from services.image_upload_service import ImageUploadService

router = APIRouter()


@router.post("/api/device/upload-image")
async def upload_device_image(
    request: Request,
    device_token: Optional[str] = Form(None),
    token: Optional[str] = Query(None),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Supports:
    1) Multipart upload (file + device_token)
    2) Raw binary upload (ESP fallback)
    """

    actual_token = device_token or token or request.headers.get("device_token")

    if not actual_token:
        raise HTTPException(status_code=400, detail="device_token is required")

    # -----------------------------
    # MODE 1: Multipart (normal)
    # -----------------------------
    if file is not None:
        return ImageUploadService.upload_image(db, actual_token, file)

    # -----------------------------
    # MODE 2: RAW (ESP fallback)
    # -----------------------------
    body = await request.body()

    if not body:
        raise HTTPException(status_code=400, detail="No image data received")

    # نحول الـ raw إلى شكل UploadFile وهمي
    from io import BytesIO
    from starlette.datastructures import UploadFile as StarletteUploadFile

    fake_file = StarletteUploadFile(
        filename="esp.jpg",
        file=BytesIO(body)
    )

    return ImageUploadService.upload_image(db, actual_token, fake_file)