# Taller · Front (React + TanStack + Clerk)

Vite + React + TanStack Router + TanStack Query + Clerk. Habla con la API FastAPI del taller.

## Verlo ya (modo demo)
```bash
npm install
npm run dev
```
Sin variables de entorno corre en **modo demo**: sin login y con datos en memoria.

## Con la API local
Con el backend corriendo (`uv run pywrangler dev`, ver `backend/README.md`):
```bash
cp .env.example .env   # trae VITE_API_URL=http://localhost:8787, sin Clerk
npm run dev
```
Sin clave de Clerk el front manda el token `demo`, que la API acepta en modo local.

## Conectarlo de verdad
Completar `VITE_CLERK_PUBLISHABLE_KEY` en `.env` (y configurar Clerk en el backend). `VITE_API_URL` puede
seguir apuntando a la API local o a la URL del Worker desplegado.

## Deploy en Cloudflare Pages
Conectar el repo de GitHub, con build command `npm run build` y output directory `dist`.
Cargar `VITE_CLERK_PUBLISHABLE_KEY` y `VITE_API_URL` (URL del Worker) en las variables del proyecto.
