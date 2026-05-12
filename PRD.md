# PRD - Ecommerce Nuevo (SDD)

## Resumen Ejecutivo

**Proyecto:** E-commerce nuevo construido desde cero  
**Usuario:** tito  
**Referencia:** Proyecto existente en `/home/tito/jesus/prograJesus/Piton/Proyetos/Ecomerece`

El proyecto anterior tenía problemas de arquitectura (mezcla API/HTML, autorización rota, tests desalineados). 
Este nuevo proyecto aplicará TDD riguroso y corrigirá todo desde el diseño.

---

## 1. Objetivos del Proyecto

1. **MVP funcional** con auth, catálogo de productos, carrito y checkout
2. **Calidad desde cero** - TDD en cada tarea, sin deuda técnica
3. **Frontend moderno** - UI coherente con paleta azul/rojo/blanco/negro
4. **Seguridad** - JWT, protección CSRF, scopes correctamente validados, seguridad contra OWASP

---

## 2. Requisitos Funcionales

### 2.1 Autenticación y Autorización

| Historia | Criterio de Éxito |
|----------|-------------------|
| Registro de usuarios | Email, password hash bcrypt, rol por defecto "user" |
| Login | JWT Bearer token + cookie HttpOnly |
| Protección de rutas | Retorna 401/403, NO None |
| Validación de scopes | Verificación por inclusión (tiene todos los requeridos) |
| Crear/editar usuarios (admin) | Solo admins pueden crear/editar |Crear un usuario admin inicial de prueba para poder crear mas usuarios con rol admin o user|

### 2.2 Catálogo de Productos

| Historia | Criterio de Éxito |
|----------|-------------------|
| Listar productos | Paginado, filtro por categoría |
| Ver detalle producto | Imagen, precio, descripción, stock |
| Crear/editar producto (admin) | Solo admins pueden crear/editar |
| Eliminar producto (admin) | Soft delete o hard delete con verificación |
| Si un producto tiene el stock bajo o es igual a 0 no se puede agregar al carrito |Se muestra un mensaje visual (toast/alerta) indicando que no hay stock|

### 2.3 Carrito de Compras

| Historia | Criterio de Éxito |
|----------|-------------------|
| Agregar al carrito | Incrementa cantidad si existe |
| Ver carrito | Lista con subtotales |
| Actualizar cantidad | 0 = eliminar item |
| Vaciar carrito | Endpoint dedicado |

### 2.4 Pedidos y Checkout

| Historia | Criterio de Éxito |
|----------|-------------------|
| Crear orden |Desde carrito, genera orden con estado "En proceso" |
| Ver pedidos usuario | Historial con estados |
| Actualizar estado  | cambia En proceso → Pagada(Una vez que el pago se realizo) |
| Actualizar estado (admin) | admin cambia Pagada → Lista → Entregada  |
| Actualizar stock de los  productos comprados en la orden | Que se elimine la card de lo productos pertinentes(user) y que admin
vea la card con algo que diga bajo stock y 
si no esta disponible|
---

## 3. Requisitos No Funcionales

- **Seguridad**: Passwords hasheadas con bcrypt, JWT con expiración, HttpOnly cookies
- **API Contract**: JSON consistente, sin mezcla HTML/JSON en mismo endpoint
- **Tests**: Coverage objetivo 70-80% (Auth 90%, Productos/Carrito/Pedidos 80%, General 70%)
- **Frontend**: Responsive, accesible (WCAG AA)
- **Logging**: Sin print() sensibles, usar logging estructurado

---

## 4. Stack Tecnológico

| Capa | Tecnología |
|------|-------------|
| Backend | FastAPI + Python 3.11 |
| ORM | SQLModel |
| DB | SQLite (dev) / PostgreSQL (prod) |
| Auth | Python-Jose (JWT) + Passlib |
| Frontend | Jinja2 + TailwindCSS |
| Tests | Pytest + pytest-asyncio |

---

## 5. Arquitectura

```
/app
├── api/
│   ├── endpoints/
│   │   ├── auth.py      # Login, register
│   │   ├── products.py  # CRUD productos
│   │   ├── cart.py      # Carrito
│   │   └── orders.py    # Pedidos
│   └── router.py        # Montaje centralizado
├── core/
│   ├── config.py        # Settings
│   └── security.py      # JWT, hash, scopes
├── db/
│   ├── base.py          # declarative base
│   ├── session.py       # async session con yield
│   └── models/          # User, Product, CartItem, Order
├── schemas/             # Pydantic models
├── services/           # Lógica de negocio
├── templates/          # Jinja2 HTML
└── main.py             # FastAPI app entrypoint
```

### Reglas de Arquitectura
- **Separación API/HTML**: Endpoints JSON en `/api/*`, vistas HTML en `/views/*`
- **Dependency Injection**: Todas las dependencias usan FastAPI `Depends()`
- **Ciclo de sesión DB**: `yield` + `close` en cada request
- **Errores**: Manejo centralizado con exception handlers

---

## 6. Roadmap por Fases (Gate en cada fase)

### Fase 0: Setup + Arquitectura Base
- [ ] Inicializar proyecto FastAPI
- [ ] Configurar DB con SQLModel async
- [ ] Definir modelos (User, Product, CartItem, Order, OrderItem)
- [ ] Configurar logging y settings
- **Gate**: Mostrar estructura de archivos → aprobar → continuar

### Fase 1: Autenticación Core
- [ ] Registro de usuarios con bcrypt
- [ ] Login con JWT (token + cookie)
- [ ] Dependencies: get_current_user (retorna 401 si inválido)
- [ ] Validación de scopes por inclusión
- **Gate**: Mostrar tests auth passing → aprobar → continuar

### Fase 2: Productos (Admin)
- [ ] CRUD productos para admin
- [ ] Listado público con paginación
- [ ] Tests TDD (RED → GREEN → REFACTOR)
- **Gate**: Mostrar coverage report → aprobar → continuar

### Fase 3: Carrito
- [ ] Agregar/actualizar/eliminar items
- [ ] Ver carrito con subtotales
- [ ] Vaciar carrito
- **Gate**: Mostrar tests carrito passing → aprobar → continuar

### Fase 4: Pedidos
- [ ] Checkout desde carrito
- [ ] Historial de pedidos por usuario
- [ ] Actualizar estado (admin)
- **Gate**: Mostrar flow e2e passing → aprobar → continuar

### Fase 5: Frontend Moderno
- [ ] Base template con TailwindCSS
- [ ] Sistema UI unificado (NO mezcla Bootstrap/Tailwind)
- [ ] Componentes: navbar, cards, tables, forms, baner, carrsuel
- **Gate**: Mostrar UI al usuario → aprobar → continuar

### Fase 6: Hardening y Release
- [ ] Lint/format/type-check en CI
- [ ] Tests de seguridad
- [ ] Documentación (runbook, contribución)
- **Gate**: Mostrar verify report → aprobar → archivar

---

## 7. Lecciones del Proyecto Anterior (Referencia)

| Problema Anterior | Solución en Nuevo Proyecto |
|-------------------|----------------------------|
| `get_current_user` retornaba None | Lanzar `HTTPException(401)` inmediatamente |
| Scopes validados incorrectamente | Validar por inclusión: `required ⊆ user.scopes` |
| Endpoints mixtos API/HTML | Separar: `/api/*` (JSON) vs `/views/*` (HTML) |
| Tests con fixtures rotos | Tests primero (TDD), fixtures determinísticos |
| Prints sensibles en código | Logging estructurado con filtro de secretos |
| `index.html` sin heredar base | Composición: base → layout → page |

---

## 8. Criterios de Éxito del Proyecto

- [ ] Todos los endpoints protegidos retornan 401/403 correctamente
- [ ] Suite de tests verde (auth, productos, carrito, pedidos)
- [ ] Cobertura 70-80% (Auth 90%, Productos/Carrito/Pedidos 80%)
- [ ] UI responsiva con paleta azul/rojo/blanco/negro
- [ ] Pipeline CI con lint + tests + type-check
- [ ] Documentación de setup y contribución

---

**Próximo paso:** Aprobación de este PRD → Iniciar Fase 0 (Setup)

---

*Documento generado desde análisis de proyecto existente + mejores prácticas SDD*