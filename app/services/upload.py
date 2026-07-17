"""Product image upload service."""

import uuid                    # Para generar nombres únicos de archivo
from pathlib import Path       # Para manejar rutas de archivos

from fastapi import HTTPException, UploadFile, status  # Para errores HTTP y recibir archivos

from app.core.config import settings  # Nuestras settings (UPLOAD_DIR, etc.)

# ─── Tipos MIME permitidos ───
# MIME = el tipo de archivo que el navegador envía en el header
ALLOWED_MIME = {
    "image/jpeg",    # .jpg .jpeg
    "image/png",     # .png
    "image/gif",     # .gif
    "image/webp",    # .webp
}

# ─── Extensiones permitidas (desde config.py) ───
# settings.ALLOWED_EXTENSIONS = "jpg,jpeg,png,gif,webp"
# .split(",") lo convierte en ["jpg","jpeg","png","gif","webp"]
# set() lo convierte en {"jpg","jpeg","png","gif","webp"} para búsqueda rápida
ALLOWED_EXT = set(settings.ALLOWED_EXTENSIONS.split(","))


async def save_upload_image(file: UploadFile) -> str:
    """
    Valida y guarda una imagen subida.
    Recibe: un archivo (UploadFile)
    Devuelve: la URL pública del archivo guardado (ej: "/static/images/products/abc123.jpg")
    """
    
    # ─── PASO 1: Validar tipo MIME ───
    # Ej: si subes un .exe, file.content_type = "application/x-msdownload"
    # Eso NO está en ALLOWED_MIME, entonces rechazamos
    if file.content_type not in ALLOWED_MIME:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,  # 400 = error del cliente
            detail=f"Tipo no permitido: {file.content_type}. Solo: jpg, png, gif, webp",
        )

    # ─── PASO 2: Validar extensión ───
    # Path(file.filename).suffix = ".jpg" (lo que está después del último punto)
    # .lower() = minúsculas
    # .lstrip(".") = quita el punto -> "jpg"
    ext = Path(file.filename).suffix.lower().lstrip(".")
    if ext not in ALLOWED_EXT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Extensión no permitida: .{ext}",
        )

    # ─── PASO 3: Leer y validar tamaño ───
    # await file.read() lee TODO el contenido del archivo en memoria
    # Esto es necesario para saber el tamaño exacto
    contents = await file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE:  # 5MB por defecto
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,  # 413 = archivo muy grande
            detail=f"Archivo demasiado grande. Máximo: {settings.MAX_UPLOAD_SIZE // (1024*1024)}MB",
        )

    # ─── PASO 4: Generar nombre único ───
    # uuid.uuid4() genera algo como "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    # .hex lo convierte en "a1b2c3d4e5f67890abcdef1234567890" (sin guiones)
    # Así evitamos que dos usuarios suban archivos con el mismo nombre
    filename = f"{uuid.uuid4().hex}.{ext}"

    # ─── PASO 5: Guardar en disco ───
    # Path(settings.UPLOAD_DIR) = "app/static/images/products"
    # .mkdir(parents=True, exist_ok=True) = crea la carpeta si no existe
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Ruta completa del archivo: app/static/images/products/a1b2c3d4.jpg
    filepath = upload_dir / filename

    # "wb" = write binary (escribe en modo binario)
    with open(filepath, "wb") as f:
        f.write(contents)

    # ─── PASO 6: Devolver URL pública ───
    # El StaticFiles de FastAPI sirve /static/ desde app/static/
    # Así que /static/images/products/a1b2c3d4.jpg → app/static/images/products/a1b2c3d4.jpg
    return f"/static/images/products/{filename}"