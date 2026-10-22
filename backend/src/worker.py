"""API del taller: lista de tareas con login (Clerk), base de datos (Neon) y mail (Resend).

Modo local: con MODO_LOCAL=1 en .dev.vars, cada servicio sin configurar se simula
(tareas en memoria, cualquier token vale, el mail se imprime en consola). Así se puede
desarrollar sin cuentas e ir conectando Neon, Clerk y Resend de a uno.
"""
import json
import time
from datetime import datetime, timezone
from urllib.parse import urlparse

import httpx
import jwt
from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from workers import WorkerEntrypoint


class Default(WorkerEntrypoint):
    async def fetch(self, request):
        import asgi

        return await asgi.fetch(app, request.js_object, self.env)


app = FastAPI(title="Taller API")


# Un error no manejado sale sin cabeceras CORS y el navegador solo muestra "Failed to fetch".
# Lo convertimos en un 500 con JSON; como se registra antes que CORS, la respuesta las lleva.
# Además, cada pedido deja una línea de log en JSON (se ve con `npx wrangler tail taller-api`).
@app.middleware("http")
async def registrar_pedido(request: Request, call_next):
    inicio = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as e:
        print(f"Error no manejado en {request.url.path}: {e!r}")
        response = JSONResponse({"detail": f"Error interno: {type(e).__name__}: {e}"}, status_code=500)
    # La plantilla de la ruta (/api/tasks/{task_id}) agrupa mejor que la URL con el id
    ruta = getattr(request.scope.get("route"), "path", request.url.path)
    print(json.dumps({
        "evento": "pedido",
        "metodo": request.method,
        "ruta": ruta,
        "status": response.status_code,
        "ms": round((time.monotonic() - inicio) * 1000),
    }))
    return response

# Usamos Authorization header (no cookies), por eso "*" alcanza para el taller.
# En producción conviene limitarlo al dominio del front.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------- Modo local
def config(env, name: str) -> str:
    """Lee una variable o secreto; devuelve "" si no está definida."""
    return getattr(env, name, None) or ""


def simulado(env, name: str) -> bool:
    """True si estamos en modo local y falta la variable que habilita el servicio real."""
    return config(env, "MODO_LOCAL") == "1" and not config(env, name)


# ---------------------------------------------------------------- Neon (SQL por HTTP)
_memoria: list[dict] = []  # "base de datos" del modo local; se pierde al reiniciar
_proximo_id = 1


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat()


async def sql_simulado(query: str, params: list) -> list[dict]:
    """Imita las 4 consultas de la API sobre una lista en memoria."""
    publica = lambda t: {k: t[k] for k in ("id", "title", "done", "created_at")}
    q = query.lstrip().split()[0].lower()
    if q == "select":
        (user_id,) = params
        return [publica(t) for t in reversed(_memoria) if t["user_id"] == user_id]
    if q == "insert":
        global _proximo_id
        user_id, title = params
        t = {"id": _proximo_id, "user_id": user_id, "title": title, "done": False, "created_at": _ahora()}
        _memoria.append(t)
        _proximo_id += 1
        return [publica(t)]
    task_id, user_id = params
    for t in _memoria:
        if t["id"] == task_id and t["user_id"] == user_id:
            if q == "update":
                t["done"] = not t["done"]
            else:  # delete
                _memoria.remove(t)
            return [publica(t)]
    return []


async def sql(env, query: str, params: list | None = None) -> list[dict]:
    """Ejecuta una consulta en Neon usando su endpoint HTTP (sin driver de Postgres)."""
    if simulado(env, "NEON_CONNECTION_STRING"):
        return await sql_simulado(query, params or [])
    conn = config(env, "NEON_CONNECTION_STRING")
    if not conn:
        raise HTTPException(500, "Falta el secreto NEON_CONNECTION_STRING (pywrangler secret put NEON_CONNECTION_STRING)")
    host = urlparse(conn).hostname
    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"https://{host}/sql",
            headers={"Neon-Connection-String": conn},
            json={"query": query, "params": params or []},
        )
    if r.status_code != 200:
        raise HTTPException(500, f"Error de base de datos: {r.text}")
    return r.json()["rows"]


# ---------------------------------------------------------------- Clerk (verificar JWT)
_keys: dict = {}  # cache de claves públicas, vive mientras viva el isolate


async def _get_key(env, kid: str):
    if kid not in _keys:
        async with httpx.AsyncClient() as client:
            r = await client.get(env.CLERK_JWKS_URL)
        r.raise_for_status()
        for k in r.json()["keys"]:
            _keys[k["kid"]] = jwt.PyJWK(k).key
    return _keys.get(kid)


async def current_user(request: Request, authorization: str = Header(default="")) -> str:
    """Devuelve el id del usuario (claim `sub`) si el token de Clerk es válido."""
    env = request.scope["env"]
    if not authorization.startswith("Bearer "):
        raise HTTPException(401, "Falta el token")
    if simulado(env, "CLERK_JWKS_URL"):
        return "usuario-local"
    token = authorization.removeprefix("Bearer ")
    try:
        kid = jwt.get_unverified_header(token)["kid"]
        key = await _get_key(env, kid)
        if key is None:
            raise HTTPException(401, "Clave desconocida")
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=env.CLERK_ISSUER,
            options={"verify_aud": False},
        )
    except jwt.PyJWTError:
        raise HTTPException(401, "Token inválido")
    return claims["sub"]


# ---------------------------------------------------------------- Rutas
class NewTask(BaseModel):
    title: str


class Welcome(BaseModel):
    email: str


@app.get("/health")
async def health():
    return {"ok": True}


@app.get("/api/me")
async def me(user_id: str = Depends(current_user)):
    return {"user_id": user_id}


@app.get("/api/tasks")
async def list_tasks(request: Request, user_id: str = Depends(current_user)):
    env = request.scope["env"]
    return await sql(
        env,
        "select id, title, done, created_at from tasks where user_id = $1 order by id desc",
        [user_id],
    )


@app.post("/api/tasks", status_code=201)
async def create_task(body: NewTask, request: Request, user_id: str = Depends(current_user)):
    env = request.scope["env"]
    rows = await sql(
        env,
        "insert into tasks (user_id, title) values ($1, $2) returning id, title, done, created_at",
        [user_id, body.title],
    )
    return rows[0]


@app.patch("/api/tasks/{task_id}")
async def toggle_task(task_id: int, request: Request, user_id: str = Depends(current_user)):
    env = request.scope["env"]
    rows = await sql(
        env,
        "update tasks set done = not done where id = $1 and user_id = $2 "
        "returning id, title, done, created_at",
        [task_id, user_id],
    )
    if not rows:
        raise HTTPException(404, "Tarea no encontrada")
    return rows[0]


@app.delete("/api/tasks/{task_id}", status_code=204)
async def delete_task(task_id: int, request: Request, user_id: str = Depends(current_user)):
    env = request.scope["env"]
    rows = await sql(
        env,
        "delete from tasks where id = $1 and user_id = $2 returning id",
        [task_id, user_id],
    )
    if not rows:
        raise HTTPException(404, "Tarea no encontrada")


# ---------------------------------------------------------------- Resend (mail de bienvenida)
@app.post("/api/welcome")
async def welcome(body: Welcome, request: Request, user_id: str = Depends(current_user)):
    """Sin dominio verificado, Resend solo permite enviar a tu propio mail (from: onboarding@resend.dev)."""
    env = request.scope["env"]
    if simulado(env, "RESEND_API_KEY"):
        print(f"[modo local] mail de bienvenida para {body.email} (no se envió)")
        return {"sent": True}
    if not config(env, "RESEND_API_KEY"):
        raise HTTPException(500, "Falta el secreto RESEND_API_KEY (pywrangler secret put RESEND_API_KEY)")
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {env.RESEND_API_KEY}"},
            json={
                "from": env.MAIL_FROM,
                "to": [body.email],
                "subject": "¡Bienvenido/a al taller!",
                "html": "<p>Tu app ya está desplegada y enviando mails 🎉</p>",
            },
        )
    if r.status_code >= 300:
        raise HTTPException(502, f"Resend respondió: {r.text}")
    return {"sent": True}
