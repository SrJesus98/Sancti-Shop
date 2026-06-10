// ==============================================
// E-COMMERCE MODERN JAVASCRIPT v2
// ==============================================

// ==================== DARK MODE ====================
(function initTheme() {
    const saved = localStorage.getItem('theme');
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

    if (saved === 'dark' || (!saved && prefersDark)) {
        document.documentElement.setAttribute('data-theme', 'dark');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
    }
})();

function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);

    // Actualizar ícono del botón
    const toggle = document.getElementById('theme-toggle');
    if (toggle) {
        toggle.innerHTML = next === 'dark' ? '🌙' : '☀️';
    }
}

// ==================== NAVBAR SCROLL EFFECT ====================
window.addEventListener('scroll', function() {
    const navbar = document.querySelector('.navbar-modern');
    if (navbar) {
        navbar.classList.toggle('scrolled', window.scrollY > 20);
    }
});

// ==================== DROPDOWN MENU ====================
let dropdownOpen = false;

function toggleDropdown() {
    dropdownOpen = !dropdownOpen;
    const menu = document.getElementById('user-dropdown');
    if (menu) {
        menu.classList.toggle('hidden');
    }
}

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
    const icons = {
        success: '✅',
        error: '❌',
        info: 'ℹ️',
        warning: '⚠️'
    };

    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 z-[200] flex items-center gap-2 ${colors[type] || colors.info} text-white px-5 py-3 rounded-xl shadow-lg`;
    toast.style.animation = 'slideIn 0.3s ease, fadeOut 0.3s ease 3.7s';
    toast.innerHTML = `${icons[type] || ''} ${message}`;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// ==================== HERO CAROUSEL ====================
function initCarousel() {
    const carousel = document.querySelector('.hero-carousel');
    if (!carousel) return;

    const slides = carousel.querySelectorAll('.slide');
    const dots = carousel.querySelectorAll('.carousel-dot');
    const prevBtn = carousel.querySelector('.carousel-btn.prev');
    const nextBtn = carousel.querySelector('.carousel-btn.next');
    let current = 0;
    let interval;

    function goTo(index) {
        slides.forEach(s => s.classList.remove('active'));
        dots.forEach(d => d.classList.remove('active'));
        current = (index + slides.length) % slides.length;
        slides[current].classList.add('active');
        dots[current].classList.add('active');
    }

    function next() { goTo(current + 1); }
    function prev() { goTo(current - 1); }

    function startAuto() {
        interval = setInterval(next, 5000);
    }

    function stopAuto() {
        clearInterval(interval);
    }

    if (prevBtn) prevBtn.addEventListener('click', () => { prev(); stopAuto(); startAuto(); });
    if (nextBtn) nextBtn.addEventListener('click', () => { next(); stopAuto(); startAuto(); });
    dots.forEach((dot, i) => {
        dot.addEventListener('click', () => { goTo(i); stopAuto(); startAuto(); });
    });

    startAuto();
}

// ==================== SCROLL ANIMATIONS ====================
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.animate-on-scroll').forEach(el => {
        observer.observe(el);
    });
}

// ==================== MODAL ====================
function showModal(options = {}) {
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay open';
    overlay.innerHTML = `
        <div class="modal-content">
            <div class="modal-icon">${options.icon || '✅'}</div>
            <h3>${options.title || ''}</h3>
            <p>${options.message || ''}</p>
            ${options.submessage ? `<p style="color: var(--text-tertiary); font-size: 0.8rem;">${options.submessage}</p>` : ''}
            <div class="modal-actions">
                ${options.showSecondary !== false ? `<button class="btn btn-secondary" onclick="closeModal(this)">${options.secondaryText || 'Seguir comprando'}</button>` : ''}
                <button class="btn btn-primary" onclick="${options.primaryAction || 'closeModal(this); window.location.href=\'/views/cart\''}">${options.primaryText || 'Ver carrito'}</button>
            </div>
        </div>
    `;
    document.body.appendChild(overlay);
}

function closeModal(el) {
    const overlay = el.closest('.modal-overlay');
    if (overlay) overlay.remove();
}

// ==================== SEARCH ====================
function initSearch(products) {
    const input = document.getElementById('search-input');
    const results = document.getElementById('search-results');
    if (!input || !results) return;

    let timeout;

    input.addEventListener('input', function() {
        clearTimeout(timeout);
        const query = this.value.trim().toLowerCase();

        if (query.length < 2) {
            results.classList.remove('active');
            results.innerHTML = '';
            return;
        }

        timeout = setTimeout(() => {
            const filtered = products.filter(p =>
                p.name.toLowerCase().includes(query) ||
                (p.category && p.category.toLowerCase().includes(query))
            ).slice(0, 6);

            if (filtered.length === 0) {
                results.innerHTML = `<div class="p-4 text-center text-sm" style="color: var(--text-tertiary);">No se encontraron productos</div>`;
            } else {
                results.innerHTML = filtered.map(p => `
                    <a href="/views/product/${p.id}" class="search-result-item">
                        <div class="result-info">
                            <h4>${p.name}</h4>
                            <span>${p.category || 'General'}</span>
                        </div>
                        <span class="result-price">$${p.price.toFixed(2)}</span>
                    </a>
                `).join('');
            }
            results.classList.add('active');
        }, 200);
    });

    // Cerrar al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!input.contains(e.target) && !results.contains(e.target)) {
            results.classList.remove('active');
        }
    });
}

// ==================== FILTERS + SORT ====================
function initFilters() {
    const chips = document.querySelectorAll('.filter-chip');
    const grid = document.getElementById('product-grid');
    const sortSelect = document.getElementById('sort-select');
    const productCount = document.getElementById('product-count');
    const activeCategory = document.getElementById('active-category');
    const activeSort = document.getElementById('active-sort');
    const activeFilters = document.getElementById('active-filters');

    let currentFilter = 'all';
    let currentSort = sortSelect?.value || 'newest';

    function getVisibleProducts() {
        const all = Array.from(grid.querySelectorAll('.product-card-modern'));
        // First filter by category
        let filtered = all;
        if (currentFilter !== 'all') {
            filtered = all.filter(p => p.dataset.category === currentFilter);
        }
        return filtered;
    }

    function sortProducts(productsArray) {
        const sorted = [...productsArray];
        switch (currentSort) {
            case 'price-asc':
                sorted.sort((a, b) => parseFloat(a.dataset.price) - parseFloat(b.dataset.price));
                break;
            case 'price-desc':
                sorted.sort((a, b) => parseFloat(b.dataset.price) - parseFloat(a.dataset.price));
                break;
            case 'name-asc':
                sorted.sort((a, b) => (a.dataset.name || '').localeCompare(b.dataset.name || ''));
                break;
            case 'name-desc':
                sorted.sort((a, b) => (b.dataset.name || '').localeCompare(a.dataset.name || ''));
                break;
            case 'newest':
            default:
                // Ya están en orden del servidor (más nuevos primero)
                break;
        }
        return sorted;
    }

    function applyFiltersAndSort() {
        const all = Array.from(grid.querySelectorAll('.product-card-modern'));

        // Hide all first
        all.forEach(p => p.style.display = 'none');

        // Get visible (by category)
        let visible = getVisibleProducts();

        // Sort visible
        visible = sortProducts(visible);

        // Show and reorder in DOM
        visible.forEach(p => p.style.display = '');

        // Reorder DOM to match sort
        visible.forEach(p => grid.appendChild(p));

        // Update product count
        const total = all.length;
        const showing = visible.length;
        if (productCount) {
            productCount.textContent = `${showing} de ${total} productos`;
        }

        // Update active filters display
        updateActiveFilters();
    }

    function updateActiveFilters() {
        if (!activeFilters || !activeCategory || !activeSort) return;

        let hasFilters = false;

        if (currentFilter !== 'all') {
            activeCategory.textContent = `Categoría: ${currentFilter}`;
            activeCategory.classList.remove('hidden');
            hasFilters = true;
        } else {
            activeCategory.classList.add('hidden');
        }

        if (currentSort !== 'newest') {
            const labels = {
                'price-asc': 'Precio ↑',
                'price-desc': 'Precio ↓',
                'name-asc': 'A-Z',
                'name-desc': 'Z-A',
            };
            activeSort.textContent = `Orden: ${labels[currentSort] || currentSort}`;
            activeSort.classList.remove('hidden');
            hasFilters = true;
        } else {
            activeSort.classList.add('hidden');
        }

        activeFilters.classList.toggle('hidden', !hasFilters);
    }

    // Category chips
    chips.forEach(chip => {
        chip.addEventListener('click', function() {
            if (this.dataset.filter === 'all') {
                chips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                currentFilter = 'all';
            } else {
                chips.forEach(c => c.classList.remove('active'));
                this.classList.add('active');
                currentFilter = this.dataset.filter;
            }
            applyFiltersAndSort();
        });
    });

    // Sort dropdown
    if (sortSelect) {
        sortSelect.addEventListener('change', function() {
            currentSort = this.value;
            applyFiltersAndSort();
        });
    }

    // Initial sort
    if (sortSelect && sortSelect.value !== 'newest') {
        currentSort = sortSelect.value;
        applyFiltersAndSort();
    }
}

// ==================== RIPPLE EFFECT ====================
function initRipple() {
    document.querySelectorAll('.ripple-btn').forEach(btn => {
        btn.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            const size = Math.max(rect.width, rect.height);

            const ripple = document.createElement('span');
            ripple.className = 'ripple-effect';
            ripple.style.width = ripple.style.height = `${size}px`;
            ripple.style.left = `${x - size/2}px`;
            ripple.style.top = `${y - size/2}px`;
            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });
}

// ==================== CART OPERATIONS ====================
async function addToCart(productId, quantity = 1) {
    try {
        const token = localStorage.getItem('access_token');
        if (!token) {
            showModal({
                icon: '🔒',
                title: 'Inicia sesión',
                message: 'Debes iniciar sesión para agregar productos al carrito',
                primaryText: 'Iniciar sesión',
                primaryAction: 'closeModal(this); window.location.href=\'/views/login\'',
                secondaryText: 'Cancelar'
            });
            return;
        }

        const response = await fetch('/api/cart/items', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({ product_id: productId, quantity })
        });

        if (response.ok) {
            const data = await response.json();
            // Obtener info del producto para el modal
            let productName = 'Producto';
            try {
                const prodRes = await fetch(`/api/products/${productId}`);
                if (prodRes.ok) {
                    const prod = await prodRes.json();
                    productName = prod.name;
                }
            } catch(e) {}

            showModal({
                icon: '✅',
                title: 'Agregado al carrito',
                message: `"${productName}" se agregó a tu carrito`,
                submessage: `Cantidad: ${quantity}`,
                primaryText: 'Ver carrito',
                primaryAction: 'closeModal(this); window.location.href=\'/views/cart\'',
                secondaryText: 'Seguir comprando'
            });
            updateCartCount();
        } else if (response.status === 401) {
            showModal({
                icon: '🔒',
                title: 'Sesión expirada',
                message: 'Tu sesión expiró. Inicia sesión de nuevo.',
                primaryText: 'Iniciar sesión',
                primaryAction: 'closeModal(this); window.location.href=\'/views/login\'',
                secondaryText: 'Cancelar'
            });
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

        const response = await fetch('/api/cart', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (response.ok) {
            const data = await response.json();
            const count = data.items ? data.items.reduce((sum, i) => sum + i.quantity, 0) : 0;
            document.querySelectorAll('.cart-count').forEach(el => {
                el.textContent = count;
                el.classList.toggle('hidden', count === 0);
            });
        }
    } catch (err) {
        // Silencio
    }
}

// ==================== SKELETON LOADING ====================
function showSkeleton(container, count = 8) {
    if (!container) return;
    container.innerHTML = '';
    for (let i = 0; i < count; i++) {
        container.innerHTML += `
            <div class="skeleton-card animate-on-scroll visible delay-${(i % 5) + 1}">
                <div class="skeleton-image"></div>
                <div class="skeleton-body">
                    <div class="skeleton-line w-75"></div>
                    <div class="skeleton-line w-50"></div>
                    <div class="skeleton-line w-40"></div>
                </div>
            </div>
        `;
    }
}

// ==================== INIT ====================
document.addEventListener('DOMContentLoaded', function() {
    // Theme toggle buttons (desktop + mobile)
    document.querySelectorAll('.theme-toggle').forEach(btn => {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        btn.innerHTML = currentTheme === 'dark' ? '🌙' : '☀️';
        btn.addEventListener('click', function(e) {
            toggleTheme();
            // Sync both buttons
            const nextTheme = document.documentElement.getAttribute('data-theme');
            document.querySelectorAll('.theme-toggle').forEach(b => {
                b.innerHTML = nextTheme === 'dark' ? '🌙' : '☀️';
            });
        });
    });

    initCarousel();
    initScrollAnimations();
    initRipple();
    initFilters();
    updateCartCount();

    // Exponer initSearch globalmente
    window.initSearch = initSearch;
});
