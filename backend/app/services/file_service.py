"""File handling service."""

from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile

from app.config import settings


def _ensure_upload_dir() -> Path:
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings.upload_dir


async def save_upload(file: UploadFile) -> tuple[str, str]:
    """Validate and persist an uploaded image file.

    Returns:
        Tuple of (original_filename, absolute_file_path).

    Raises:
        HTTPException 400 on validation failure.
    """
    # Validate content type
    content_type = file.content_type or ""
    if content_type not in settings.allowed_mime_types:
        raise HTTPException(
            status_code=400,
            detail=f"Tipo de fichero no permitido: {content_type}. "
                   f"Se aceptan: {', '.join(settings.allowed_mime_types)}",
        )

    # Read content
    content = await file.read()

    # Validate size
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"El fichero supera el límite de {settings.max_upload_size_bytes // (1024*1024)} MB",
        )

    # Validate it is actually an image using magic bytes
    _validate_magic_bytes(content, content_type)

    # Build unique filename
    ext_map = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
    extension = ext_map.get(content_type, ".jpg")
    unique_name = f"{uuid.uuid4().hex}{extension}"

    upload_dir = _ensure_upload_dir()
    file_path = upload_dir / unique_name
    file_path.write_bytes(content)

    original_filename = file.filename or unique_name
    return original_filename, str(file_path)


def _validate_magic_bytes(content: bytes, declared_mime: str) -> None:
    """Check file magic bytes match declared MIME type."""
    if len(content) < 4:
        raise HTTPException(status_code=400, detail="Fichero demasiado pequeño")

    jpeg_magic = content[:3] == b"\xff\xd8\xff"
    png_magic = content[:8] == b"\x89PNG\r\n\x1a\n"
    webp_magic = content[:4] == b"RIFF" and content[8:12] == b"WEBP"

    valid = (
        (declared_mime == "image/jpeg" and jpeg_magic)
        or (declared_mime == "image/png" and png_magic)
        or (declared_mime == "image/webp" and webp_magic)
    )
    if not valid:
        raise HTTPException(
            status_code=400,
            detail="El contenido del fichero no coincide con el tipo declarado",
        )
