# Del código a producción: desplegá tu app con herramientas gratuitas

Taller práctico de **JCSA**. Vas a desplegar una app web completa (lista de tareas con login) usando solo planes gratuitos.

> **Los planes gratuitos y sus límites cambian.** Revisá las páginas oficiales de cada servicio antes de depender de ellos en un proyecto propio.

## Para quién es

Estudiantes de informática, sistemas o carreras afines, y cualquiera que quiera llevar sus proyectos a producción sin costo.

**Conocimientos previos:** programación básica (idealmente algo de Python y JavaScript), nociones de Git/GitHub y de qué es una API.

Al terminar vas a tener tu propia app funcionando en internet y vas a saber replicar el proceso en tus proyectos.

## Qué vamos a construir

```
Navegador ── React + TanStack ──► Cloudflare Workers (assets estáticos)
    │
    └─► API FastAPI (Python) ──► Cloudflare Workers
              ├─► Neon (Postgres)
              ├─► Clerk (verifica el login)
              ├─► Resend (mail de bienvenida)
              └─► Grafana Cloud (monitoreo)
```

| Capa | Herramienta |
|---|---|
| Front | React + Vite + TanStack Router y Query, en Cloudflare Workers (assets estáticos) |
| Backend | FastAPI en Cloudflare Workers (Python) |
| Base de datos | Neon (Postgres serverless) |
| Autenticación | Clerk |
| Mails | Resend |
| Monitoreo | Grafana Cloud |

## Estructura del repo

```
frontend/   app React (tiene su propio README)
backend/    API FastAPI (tiene su propio README)
```

---

## 1. Antes del taller (obligatorio)

Hacerlo **antes** del evento, porque crear cuentas en el momento consume mucho tiempo.

### Cuentas gratuitas
- [ ] GitHub
- [ ] Cloudflare
- [ ] Neon
- [ ] Clerk
- [ ] Resend
- [ ] Grafana Cloud

### Software
- [ ] Git
- [ ] Node.js 22.12 o superior, recomendado 24 LTS (`node -v`)
- [ ] Python 3.12 o superior (`python --version`)
- [ ] [uv](https://docs.astral.sh/uv/) 0.12.3 o superior (`uv --version`; para actualizar: `uv self update`)
- [ ] Un editor de código (VS Code, por ejemplo)

### Preparación
- [ ] Hacer **fork** de este repositorio y clonarlo en tu computadora
- [ ] Correr `npm install` dentro de `frontend/` y `uv sync` dentro de `backend/`
- [ ] Probar que todo arranca en local, sin cuentas (ver `backend/README.md`):
  `uv run pywrangler dev` en `backend/` (la primera vez descarga Python 3.13 para Workers) y `npm run dev` en `frontend/`

---

## 2. Agenda (aprox. 2 h 30)

| Bloque | Min | Qué hacemos | Listo cuando... |
|---|---|---|---|
| 0 | 15 | Arquitectura y chequeo de cuentas | Todos tienen sus cuentas y el repo clonado |
| 1 | 30 | Front en Cloudflare | La app abre en una URL `*.workers.dev` |
| 2 | 30 | API FastAPI + Neon | `/health` responde y `/api/tasks` devuelve datos |
| 3 | 25 | Login con Clerk | Solo un usuario logueado ve sus tareas |
| 4 | 15 | Mail con Resend | Llega el mail de bienvenida |
| 5 | 25 | Monitoreo con Grafana Cloud | Se ve actividad de la API en un panel |
| 6 | 10 | Cierre y dudas | |

---

## 3. Paso a paso

### Bloque 1 · Front (Cloudflare)
1. Probar local: `cd frontend && npm run dev`. Sin variables de entorno arranca en **modo demo**.
2. En Cloudflare: *Workers & Pages → Create → Import a repository* y elegir tu fork.
3. Configurar (el directorio de salida ya está en `frontend/wrangler.jsonc`):
   - *Project name*: `taller-frontend` (el mismo `name` de `frontend/wrangler.jsonc`)
   - *Build command*: `npm run build`
   - *Deploy command*: `npx wrangler deploy`
   - *Non-production branch deploy command*: `npx wrangler versions upload`
   - *Path* (root directory): `frontend`
4. Las variables `VITE_*` se cargan en *Settings → Build → Variables and secrets* (son de build, no de runtime).

### Bloque 2 · API y base de datos
1. En Neon: crear un proyecto, abrir el **SQL Editor**, ejecutar `backend/schema.sql` y copiar la *connection string*.
2. `cd backend && cp .dev.vars.example .dev.vars`. Así viene en **modo local** (todo simulado):
   `uv run pywrangler dev` y probar `curl http://localhost:8787/health`.
3. Completar `NEON_CONNECTION_STRING` en `.dev.vars`, reiniciar y verificar que las tareas se guardan en Neon.
4. Cargar el secreto y desplegar:
   ```bash
   uv run pywrangler secret put NEON_CONNECTION_STRING
   uv run pywrangler deploy
   ```
5. En el front, poner la URL del Worker en `VITE_API_URL`.

### Bloque 3 · Login (Clerk)
1. En Clerk: crear una aplicación y copiar la **publishable key** y la **Frontend API URL**.
2. Front: `VITE_CLERK_PUBLISHABLE_KEY` en `frontend/.env` y en las variables de build del front en Cloudflare.
3. Backend: completar `CLERK_ISSUER` y `CLERK_JWKS_URL` en `backend/wrangler.jsonc` (reemplazar `TU-INSTANCIA`) y volver a desplegar.
4. Probar: iniciar sesión y crear una tarea. Con otro usuario no deberías ver esa tarea.

### Bloque 4 · Mails (Resend)
1. En Resend: crear una **API key**.
2. `uv run pywrangler secret put RESEND_API_KEY`
3. Sin dominio verificado, Resend solo permite enviar **a tu propio mail** (remitente `onboarding@resend.dev`).
4. En la app, escribir tu mail y apretar *Enviar*.

### Bloque 5 · Monitoreo (Grafana Cloud)
`[Completar: definir y probar el flujo exacto antes del evento]`

Objetivo: crear el stack gratuito en Grafana Cloud, conectar los logs o métricas del Worker y armar un panel básico que muestre las peticiones a la API.

---

## 4. Problemas comunes

| Síntoma | Qué revisar |
|---|---|
| `401` en la API | Que `CLERK_ISSUER` y `CLERK_JWKS_URL` coincidan con tu instancia de Clerk |
| El front no llega a la API | Que `VITE_API_URL` apunte al Worker desplegado (no a `localhost`) |
| Error de base de datos | Que `NEON_CONNECTION_STRING` esté cargada como secreto y que `schema.sql` se haya ejecutado |
| El mail no llega | Revisar spam y que el destinatario sea tu propio mail (sin dominio verificado) |
| Cambié una variable `VITE_*` y no pasa nada | Tienen que estar en las variables de **build** y hay que volver a desplegar el front |

**Plan B:** si falla algún servicio, volvé a dejar vacía su variable en `.dev.vars` (con `MODO_LOCAL=1` se simula) o usá el **modo demo** del front (sin variables de entorno) para seguir el hilo del taller.

---

## 5. Seguridad básica
- Nunca subas `.env` ni `.dev.vars` a Git (ya están en `.gitignore`).
- Los secretos del Worker se cargan con `pywrangler secret put`, no en `wrangler.jsonc`.
- En el backend, CORS está abierto (`*`) para simplificar el taller. En un proyecto real conviene limitarlo al dominio de tu front.

## Contacto
`[Completar: nombre y correo de contacto]`