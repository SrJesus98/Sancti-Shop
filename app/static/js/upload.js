async function uploadImage(file) {
    const formData = new FormData();
    formData.append('file', file);

    const token = localStorage.getItem('access_token');
    const btn = document.getElementById('upload-btn');
    const status = document.getElementById('upload-status');
    const inputUrl = document.getElementById('inputImageUrl');

    btn.disabled = true;
    status.textContent = 'Subiendo...';
    status.className = 'text-blue-600 text-sm';

    try {
        const res = await fetch('/api/upload', {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` },
            body: formData,
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || 'Error al subir');
        }

        const data = await res.json();
        inputUrl.value = data.url;
        previewImage(data.url);
        status.textContent = '✅ Imagen subida correctamente';
        status.className = 'text-green-600 text-sm';
    } catch (err) {
        status.textContent = '❌ ' + err.message;
        status.className = 'text-red-600 text-sm';
    } finally {
        btn.disabled = false;
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const fileInput = document.getElementById('image-file');
    const uploadBtn = document.getElementById('upload-btn');

    if (fileInput && uploadBtn) {
        uploadBtn.addEventListener('click', function() {
            const file = fileInput.files[0];
            if (!file) {
                alert('Selecciona un archivo primero');
                return;
            }
            uploadImage(file);
        });

        fileInput.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    const container = document.getElementById('imagePreviewContainer');
                    preview.src = e.target.result;
                    container.classList.remove('hidden');
                };
                reader.readAsDataURL(file);
            }
        });
    }
});
