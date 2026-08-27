# Deploy de staging

## Estado actual

- Repositorio: `SrJesus98/Sancti-Shop`
- Rama de staging: `feature/deploy-produccion`
- Rama destino futura: `main`
- Proveedor elegido: Render
- Base de datos de staging: PostgreSQL en Render
- Estado de la base de datos: `Available`
- Web Service: todavía no creado
- Commit preparado para staging: `0273ca9 chore(deploy): prepare staging environment`
- Estado local confirmado: árbol de trabajo limpio después del push

El flujo previsto es:

```text
feature/deploy-produccion -> Render staging -> pruebas -> main -> producción
```

## Crear el Web Service en Render

En Render, seleccionar **New + > Web Service** y conectar el repositorio de GitHub
`SrJesus98/Sancti-Shop`.

Usar estos valores:

| Campo | Valor |
| --- | --- |
| Name | `sancti-shop-staging` |
| Branch | `feature/deploy-produccion` |
| Runtime | `Python 3` |
| Root Directory | dejar vacío, porque el proyecto está en la raíz |
| Build Command | `pip install .` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Plan | `Free`, si está disponible |

No usar `run.sh` como comando de inicio en Render: crea un entorno virtual y
activa `--reload`, ambos comportamientos son propios del desarrollo local.

## Variables de entorno

Configurar estas variables en **Environment** del Web Service:

| Variable | Valor para staging |
| --- | --- |
| `DATABASE_URL` | Internal Database URL de la base PostgreSQL de Render |
| `DEBUG` | `false` |
| `ENVIRONMENT` | `staging` |
| `SECRET_KEY` | valor aleatorio largo y privado |
| `CORS_ORIGINS` | URL pública del Web Service, sin barra final |
| `FRONTEND_URL` | URL pública del Web Service |
| `PAYMENT_PROVIDER` | `mock` |
| `PAYMENT_MODE` | `sandbox` |
| `PAYMENT_WEBHOOK_SECRET` | valor privado específico de staging |

No subir secretos al repositorio ni ponerlos en este archivo. La `DATABASE_URL`
debe copiarse desde Render usando la URL interna de la base de datos, no una URL
de conexión escrita manualmente.

## Orden recomendado

1. Crear el Web Service y seleccionar la rama `feature/deploy-produccion`.
2. Configurar los comandos de build e inicio.
3. Crear las variables de entorno anteriores.
4. Crear el servicio y esperar a que termine el primer deploy.
5. Abrir `https://<servicio>.onrender.com/health` y comprobar que responde con
   `{"status":"ok"}`.
6. Abrir la aplicación en `/views/` y probar registro, login, catálogo, carrito,
   checkout y panel administrativo.
7. Revisar los logs de Render si el deploy falla.

## Comprobaciones locales antes del deploy

Desde la raíz del repositorio:

```bash
git switch feature/deploy-produccion
git pull origin feature/deploy-produccion
pytest -x -q
```

El comando de inicio equivalente para una prueba local de producción es:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Puntos pendientes antes de producción

- Cambiar `DATABASE_URL` por una base PostgreSQL de producción independiente.
- Generar secretos diferentes para producción.
- Revisar el seed: actualmente crea usuarios demo con credenciales conocidas al
  iniciar una base vacía.
- Mantener `PAYMENT_PROVIDER=mock` en staging; la integración de Enzona todavía
  es un stub y no realiza pagos reales.
- Definir almacenamiento persistente externo para las imágenes subidas por los
  administradores. El disco local del Web Service no debe tratarse como
  almacenamiento permanente.
- Configurar un dominio y valores de CORS/Frontend específicos de producción.
- Hacer merge a `main` únicamente después de validar staging.

## Comandos Git de referencia

Verificar la rama y el estado:

```bash
git branch --show-current
git status
```

Publicar cambios posteriores:

```bash
git add .
git commit -m "tipo(alcance): descripción breve"
git push origin feature/deploy-produccion
```
