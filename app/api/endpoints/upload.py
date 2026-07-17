"""Image upload endpoint."""

from fastapi import APIRouter, Depends, UploadFile  # APIRouter para crear rutas, Depends para auth

from app.api.dependencies.auth import require_scopes  # Para proteger la ruta (solo admin)
from app.db.models import User                        # El modelo User (para el tipo del Depends)
from app.services.upload import save_upload_image     # Nuestro service recién creado

# ─── Router ───
# prefix="/upload" hace que todas las rutas empiecen con /api/upload
router = APIRouter(prefix="/upload", tags=["upload"])


# ─── POST /api/upload ───
# file: UploadFile → FastAPI recibe el archivo del formulario automáticamente
# _: User = Depends(require_scopes(["admin:products"])) → solo admin puede subir
# El "_" significa "no me importa el valor, solo quiero que se ejecute la dependencia"
@router.post("")
async def upload_image(
    file: UploadFile,
    _: User = Depends(require_scopes(["admin:products"])),
):
    """
    Sube una imagen al servidor.
    Recibe: multipart/form-data con un campo "file"
    Devuelve: {"filename": "original.jpg", "url": "/static/images/products/uuid.jpg"}
    """
    # Delegar toda la lógica al service
    url = await save_upload_image(file)
    
    # Devolver el nombre original + la URL pública
    return {"filename": file.filename, "url": url}