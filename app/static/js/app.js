// E-commerce Frontend JavaScript

// ==================== DROPDOWN MENU ====================
let dropdownOpen = false;

function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
    const menu = document.getElementById('user-dropdown');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// Cerrar dropdown al hacer clic fuera
document.addEventListener('click', function(event) {
    const menu = document.getElementById('user-menu');
    if (menu && !menu.contains(event.target)) {
        const dropdown = document.getElementById('user-dropdown');
        if (dropdown && !dropdown.classList.contains('hidden')) {
            dropdown.classList.add('hidden');
            dropdownOpen = false;
        }
    }
});

// ==================== MOBILE MENU ====================
function toggleMobileMenu() {
    const menu = document.getElementById('mobile-menu');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'success') {
    const colors = {
        success: 'bg-green-500',
        error: 'bg-red-500',
        info: 'bg-blue-500',
        warning: 'bg-yellow-500'
    };

    const toast = document.createElement('div');
    toast.className = `toast ${colors[type] || colors.info} text-white px-6 py-3 rounded-lg shadow-lg`;
    toast.textContent = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ==================== CART OPERATIONS ====================
async function addToCart(productId, quantity = 1) {
    try {
        const token = localStorage.getItem('access_token');
        const response = await fetch('/api/cart/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ product_id: productId, quantity })
        });

        if (response.ok) {
            showToast('Producto agregado al carrito ✅', 'success');
            // Actualizar contador del carrito
            updateCartCount();
        } else if (response.status === 401) {
            showToast('Debes iniciar sesión primero', 'warning');
            window.location.href = '/views/login';
        } else {
            const data = await response.json();
            showToast(data.detail || 'Error al agregar al carrito', 'error');
        }
    } catch (err) {
        showToast('Error de conexión', 'error');
    }
}

async function updateCartCount() {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) return;

        const response = await fetch('/api/cart/items', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            const count = data.items ? data.items.length : 0;
            document.querySelectorAll('.cart-count').forEach(el => {
                el.textContent = count;
                el.classList.toggle('hidden', count === 0);
            });
        }
    } catch (err) {
        // Silencio
    }
}
