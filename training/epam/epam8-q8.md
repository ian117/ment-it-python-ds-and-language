# P8 — Diseño de endpoints REST · RESUELTO

> "¿Cuál sería tu diseño de endpoints siguiendo REST?"
> Lo respondiste dibujando las rutas en papel con sus status codes, nombres de recursos, método HTTP y algo de DTOs. **Ese es el enfoque correcto.** Aquí está completo.

**La regla que gobierna todo:** los recursos son **sustantivos en plural**, el **verbo lo pone HTTP**, y la **jerarquía expresa pertenencia**.

---

## 1. La tabla de endpoints

```
GET    /api/v1/tasks?status=open&page=1&limit=20   200
POST   /api/v1/tasks                               201 + header Location
GET    /api/v1/tasks/{id}                          200 | 404
PUT    /api/v1/tasks/{id}                          200        (reemplazo total)
PATCH  /api/v1/tasks/{id}                          200        (parcial)
DELETE /api/v1/tasks/{id}                          204

GET    /api/v1/tasks/{id}/shares                   200
POST   /api/v1/tasks/{id}/shares                   201   body: {user_id, role}
PATCH  /api/v1/tasks/{id}/shares/{user_id}         200   body: {role}
DELETE /api/v1/tasks/{id}/shares/{user_id}         204

GET    /api/v1/me/tasks?filter=shared_with_me      200
```

Tres decisiones que conviene justificar:

- **`/tasks/{id}/shares`** — los shares son un sub-recurso de la tarea, no una entidad global. No existe `/shares/{id}` porque un share no tiene sentido fuera de su tarea.
- **`PUT` vs `PATCH`** — `PUT` reemplaza el recurso entero (los campos que omitas se borran); `PATCH` actualiza solo lo que mandas. Si solo vas a soportar uno, soporta `PATCH`.
- **`/me`** — alias del usuario autenticado. Evita `/users/{id}/tasks`, donde alguien puede poner el `id` de otro (y ahí empieza el IDOR).

---

## 2. Por qué esas rutas están mal

| Ruta | Problema |
|---|---|
| `/getTasks` | El verbo va en el método HTTP, no en la URL. `GET /tasks` ya dice "obtener". |
| `/api/v1/task/create` | Dos errores: singular (`task`) y verbo en la ruta. Es `POST /tasks`. |
| `POST /api/v1/deleteTask/5` | Usa POST para todo. Es `DELETE /tasks/5`. |

**Por qué importa más allá del estilo:** los verbos HTTP tienen semántica que la infraestructura entiende. Un `GET` es cacheable por proxies y CDNs; un `DELETE` es idempotente, así que un reintento tras un timeout es seguro. Si metes todo en `POST`, pierdes esas garantías y ningún intermediario puede optimizar nada.

Un cuarto error que penaliza igual: **devolver `200` con `{"error": "..."}` dentro**. El status code *es* el resultado. Un cliente que solo mira el código creerá que todo salió bien.

---

## 3. Status codes

| Code | Cuándo |
|---|---|
| 200 | OK con cuerpo |
| 201 | Creado (+ header `Location` apuntando al recurso nuevo) |
| 204 | OK sin cuerpo (típico de `DELETE`) |
| 400 | Petición malformada — JSON inválido, no parsea |
| 401 | No autenticado |
| 403 | Autenticado, pero sin permiso |
| 404 | No existe |
| 409 | Conflicto — ya está compartido con ese usuario |
| 422 | Sintaxis bien, semántica mal (validación de campos) |
| 429 | Rate limit |
| 500 | Error nuestro |

**401 vs 403 vs 404** — la forma corta de recordarlo:
- **401** = "no sé quién eres" → falta el token, o está expirado/inválido. La respuesta correcta del cliente es *autenticarse*.
- **403** = "sé quién eres, y no puedes" → el token es válido pero te faltan permisos. Reintentar con el mismo token no sirve de nada.
- **404** = "eso no existe" (o no quiero decirte si existe).

**400 vs 422** — la línea está en si el servidor **pudo entender** el cuerpo:
- `400`: el JSON está roto, falta una llave, el Content-Type no cuadra. No llegué ni a mirar los campos.
- `422`: el JSON parsea perfecto, pero `due_date` está en el pasado o `role` vale `"superadmin"`. Entendí la petición y la rechacé por su contenido.

**404 en vez de 403, a propósito.** Si devuelves 403 al pedir `/tasks/9182`, acabas de confirmar que esa tarea existe. Un atacante itera IDs y mapea qué recursos hay, aunque no pueda leerlos — eso es un **oráculo de existencia**. Devolviendo 404 no filtras nada. El trade-off es que depurar se vuelve más confuso para usuarios legítimos, así que se suele aplicar solo a recursos sensibles.

---

## 4. DTOs

```python
class TaskCreateDTO(BaseModel):      # ENTRADA: solo lo que el cliente puede mandar
    title: str
    description: str | None = None
    due_date: date | None = None

class TaskResponseDTO(BaseModel):    # SALIDA: solo lo que el cliente debe ver
    id: int
    title: str
    status: str
    owner: UserSummaryDTO
    my_role: str
```

**Por qué no exponer la entidad de BD, en tres razones:**

1. **Previene mass assignment.** Si construyes la entidad directamente desde el body, alguien manda `{"title": "x", "owner_id": 99, "is_admin": true}` y acaba de reasignar la tarea o escalar privilegios. El DTO de entrada **descarta silenciosamente** cualquier campo que no declare. Este es el ataque concreto que la pregunta busca.
2. **Desacopla la API de la BD.** Puedes renombrar una columna o partir una tabla sin romper a tus clientes. Sin DTO, tu esquema de base de datos *es* tu contrato público.
3. **Evita filtrar datos.** La entidad `User` tiene `password_hash`. Serializarla entera lo publica.

**Campos que nunca se aceptan del cliente:** `id`, `owner_id`, `created_at`, `updated_at`, `is_admin`, `status` cuando lo controla el flujo de negocio. Regla: cualquier cosa que decida el **servidor** o que determine **permisos** no viene del body.

---

## 5. Los extras que rematan

- **Versionado**: `/api/v1` en la ruta. Existen alternativas (header `Accept`, query param), pero la ruta es la más pragmática: se ve en los logs, se prueba desde el navegador y no hay ambigüedad.
- **Paginación**: `limit`/`offset` para empezar, cursor cuando la tabla crece (ver P7).
- **Filtrado y orden** por query params: `?status=open&sort=-due_date`.
- **Formato de error consistente**: RFC 7807 `application/problem+json`, con `type`, `title`, `status`, `detail`. Un solo formato para toda la API.
- **Idempotencia**: `GET`, `PUT` y `DELETE` **son** idempotentes — repetirlos deja el sistema en el mismo estado. `POST` **no**: dos llamadas crean dos tareas. Si necesitas que lo sea (pagos, reintentos automáticos), el cliente manda un header `Idempotency-Key: <uuid>` y el servidor guarda la respuesta asociada a esa clave y la reutiliza si la ve de nuevo.

---

## 6. (E13) Los tres endpoints

```
GET    /api/v1/tasks/{id}/shares              200 | 401 403 404
DELETE /api/v1/tasks/{id}/shares/{user_id}    204 | 401 403 404   (el owner revoca)
DELETE /api/v1/tasks/{id}/shares/me           204 | 401 404       (yo abandono)
```

**¿Por qué los dos últimos no son el mismo endpoint, si la ruta casi coincide?** Porque la **autorización es distinta**:

- Revocar el share de otro exige ser **owner** de la tarea → puede dar `403`.
- Abandonar exige únicamente **ser tú mismo** → no hay `403` posible; cualquiera puede renunciar a su propio acceso.

Si los unificas en `DELETE .../shares/{user_id}`, el chequeo se vuelve un `if user_id == current_user or is_owner(...)` dentro del handler — y esa clase de condicional mezclando dos políticas es exactamente donde se cuelan los bugs de permisos. `/me` como alias explícito documenta la intención y evita que un dedazo en el `user_id` borre el acceso de otra persona.

Dos matices más:
- Revocar un share inexistente puede devolver `404` o `204` (idempotente). Ambas son defendibles **si eres consistente** en toda la API.
- El owner no puede eliminarse a sí mismo por esta ruta: para eso sería una **transferencia de propiedad** (`PATCH /tasks/{id}` con el nuevo `owner_id`).

---

## 7. 💬 (E14) El `viewer` que pudo hacer PATCH

**Dónde estuvo el fallo:** en la **autorización a nivel de recurso**. Casi seguro el middleware verificó que el usuario está autenticado y quizá que tiene *algún* acceso a la tarea, pero nunca comparó su **rol sobre esa tarea concreta** con la acción solicitada. Ser `viewer` de `task1` te da acceso de lectura, no de escritura.

**En qué capa se arregla:** en la capa de **autorización/servicio**, antes de mutar. Se resuelve el rol efectivo del usuario sobre ese recurso y se exige `owner` o `editor`:

```python
@router.patch("/tasks/{id}")
def update(id: int, dto: TaskUpdateDTO,
           user = Depends(require_task_role(id, {"owner", "editor"}))):
    ...
```

**Dónde jamás se arregla:** en el frontend. Ocultar el botón de editar no es seguridad — la petición se manda igual con curl. Y tampoco basta con arreglarlo solo en el controlador de `PATCH`: si la regla vive en cada handler, el próximo endpoint que alguien escriba la olvidará. Va centralizado.

**Qué debía devolver:** **403** (o **404** si prefieres no revelar que la tarea existe).

**Cómo se llama:** **IDOR** (Insecure Direct Object Reference), o **BOLA** (Broken Object Level Authorization) en la nomenclatura del OWASP API Security Top 10, donde ocupa el **puesto #1**. Es la vulnerabilidad más común en APIs, precisamente porque el chequeo por ruta *parece* suficiente.
