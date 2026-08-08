# Guía de estudio — Entrevista técnica EPAM

Archivo autosuficiente. Cubre las 12 preguntas de la entrevista, en el orden en que las hicieron.

**Cómo usar este archivo**
1. Lee la sección 1 (explicación de temas).
2. Ve a la sección 2, tapa las respuestas y contesta tú primero.
3. Haz los ejercicios de la sección 3 sin mirar la 4.
4. Marca el checklist final; lo que no marques, es tu tema débil.

---

## 0. Índice: qué te preguntaron y qué evalúa

| # | Lo que te preguntaron | Temas |
|---|---|---|
| P1 | Promedio de temperatura por ciudad desde una lista de tuplas | Agregación, `defaultdict`, complejidad |
| P2 | ¿Qué imprime `d.my_method()` con herencia múltiple `D(B, C)`? | MRO / C3, diamante, `ABC`, `super()` |
| P3 | Añadir 'preproc' y 'postproc' a un método que no puedes modificar | Decoradores, `functools.wraps`, monkey patching |
| P4 | Manejar Error1 → e1, Error2 → e2, cualquier otro → any | Jerarquía de excepciones, orden de `except` |
| P5 | Diseño que soporte extracción de noticias por scraping **y** por API | SOLID, ABC como contrato, Strategy, Adapter |
| P6 | Estrategia de testing de eso, librerías, y cómo evitar gastar dinero llamando la API real | Pirámide de tests, mocks, VCR, caché, rate limit |
| P7 | Schema de BD que soporte compartir tareas entre usuarios | N:M, tabla pivote, roles, índices |
| P8 | Diseño de endpoints siguiendo REST | Recursos, verbos, status codes, DTOs |
| P9 | Autenticación: JWT, sesiones, dónde se guarda el token, roles | JWT, cookies, RBAC, refresh tokens |
| P10 | Orquestar con Docker/Compose: app TMS, email service, Postgres, Redis | Compose, volumes, networks, healthchecks |
| P11 | Lo mismo, pero con servicios cloud | ECS/EKS, RDS, ElastiCache, SQS, IaC |
| P12 | ¿Cómo usarías AI en tu trabajo? | Criterio, límites, seguridad |

**Bloques**: P1–P4 Python core/OOP · P5–P6 Diseño y testing · P7–P9 Datos, API y auth · P10–P11 Infra · P12 Cultural.

---

# 1. Explicación de los temas

## 1.1 Agregación de datos (P1)

El patrón es siempre el mismo: **una pasada, acumular en un dict, reducir al final**.

```python
from collections import defaultdict
from statistics import mean

data = [("mx", 30), ("ny", 10), ("mx", 20)]

# A) Guardar todos los valores: más memoria, más flexible
buckets = defaultdict(list)
for city, temp in data:
    buckets[city].append(temp)
result = {city: mean(temps) for city, temps in buckets.items()}

# B) Acumular suma y conteo: O(1) de memoria por ciudad  <- la preferida
sums, counts = defaultdict(float), defaultdict(int)
for city, temp in data:
    sums[city] += temp
    counts[city] += 1
result = {city: sums[city] / counts[city] for city in sums}
```

Puntos que suman:
- **Complejidad**: O(n) tiempo, O(k) memoria (k = ciudades únicas). Ordenar + `itertools.groupby` sería O(n log n) → peor.
- `defaultdict` vs `dict.setdefault()` vs `dict.get(key, 0)`: los tres valen; `defaultdict` es el idiomático.
- `Counter` **no** promedia, solo cuenta ocurrencias. Sirve para el `counts`.
- Casos borde: lista vacía, normalizar la clave (`city.strip().lower()`), redondeo, `mean([])` lanza `StatisticsError`.

> **Analogía**: contar propinas por mesero. No necesitas guardar cada billete; basta un papelito por mesero con "total acumulado / número de propinas".

## 1.2 MRO y herencia múltiple (P2)

Cuando llamas `d.my_method()`, Python recorre una lista lineal de clases: el **MRO** (Method Resolution Order), calculado con **C3 linearization**.

Reglas de C3, en corto:
1. La clase misma va primero.
2. Se respeta el orden de declaración de las bases, de izquierda a derecha.
3. Una clase nunca aparece antes que sus subclases.

```python
class D(B, C): ...
D.__mro__   # (D, B, C, A, ABC, object)
```

Como `B` va antes que `C`, gana `B`. En el **problema del diamante** (A arriba, B y C en medio, D abajo), A aparece **una sola vez**, al final.

`super()` **no significa "mi clase padre"**: significa "la siguiente clase en el MRO del objeto real". Por eso en herencia múltiple todas las clases deben llamar a `super().__init__(...)`; si no, ramas enteras se quedan sin inicializar.

```python
class A:
    def __init__(self, **kw): super().__init__(**kw)      # cooperativo
class B(A):
    def __init__(self, b=1, **kw): self.b = b; super().__init__(**kw)
class C(A):
    def __init__(self, c=2, **kw): self.c = c; super().__init__(**kw)
class D(B, C): pass

d = D()   # d.b y d.c existen: B.__init__ -> super() -> C.__init__ -> A
```

Clases abstractas:

```python
from abc import ABC, abstractmethod

class A(ABC):
    @abstractmethod
    def my_method(self): ...
```

- `ABC` es azúcar de `metaclass=ABCMeta`.
- Instanciar con métodos abstractos sin implementar → `TypeError: Can't instantiate abstract class`.
- El chequeo ocurre **al instanciar**, no al definir.

> **Analogía**: el MRO es a quién le preguntas cuando no sabes algo: primero a ti, luego al hermano mayor (B), luego al de en medio (C), luego a papá (A). `super()` es "pásale la pregunta al siguiente de la fila", no "pregúntale a papá directo".

## 1.3 Decoradores y envolver comportamiento (P3)

Un decorador es una función que recibe una función y devuelve otra que la envuelve.

```python
import functools

def with_hooks(func):
    @functools.wraps(func)          # conserva __name__, __doc__, firma
    def wrapper(*args, **kwargs):
        print("preproc")
        result = func(*args, **kwargs)
        print("postproc")
        return result
    return wrapper
```

Si **no puedes tocar** el código de la clase:

| Técnica | Cómo | Cuándo |
|---|---|---|
| Monkey patching | `D.my_method = with_hooks(D.my_method)` | No puedes tocar la clase; afecta a **todas** las instancias |
| Decorar la instancia | `d.my_method = with_hooks(d.my_method)` | Solo esa instancia |
| Subclase | `class E(D): def my_method(self): print("pre"); super().my_method(); print("post")` | La forma limpia si controlas quién instancia |
| Decorador de clase | `@decorate_all` reasigna todos sus métodos | Muchos métodos a la vez |
| `__getattribute__` / proxy | Interceptas cualquier acceso a atributo | Genérico, potente, difícil de depurar |
| Context manager | `with hooks(): d.my_method()` | El pre/post es del *bloque*, no del método |

`functools.wraps` importa: sin él, `wrapper.__name__` es `"wrapper"` y se rompen introspección, docs y varios frameworks.

> **Analogía**: el decorador es papel de regalo. El objeto de dentro no cambia; solo lo que ves al recibirlo y al abrirlo. `functools.wraps` es pegarle la etiqueta original al paquete.

## 1.4 Manejo de excepciones por tipo (P4)

Jerarquía: `BaseException` → `Exception` → todo lo demás (`ValueError`, `KeyError`, `TypeError`, `OSError`…). `KeyboardInterrupt` y `SystemExit` cuelgan de `BaseException`, **no** de `Exception`; por eso `except Exception` no las atrapa, y está bien así.

```python
try:
    d.my_method()
except Error1 as exc:            # más específico primero
    handle_e1(exc)
except (Error2, Error3) as exc:  # varios tipos, mismo manejo
    handle_e2(exc)
except Exception as exc:         # fallback
    handle_any(exc)
else:
    print("no hubo error")       # solo si el try no lanzó
finally:
    cleanup()                    # siempre
```

- **El orden importa**: gana el primer `except` cuyo tipo haga match por `isinstance`. Si `except Exception` va arriba, lo de abajo es código muerto.
- `except:` desnudo es mala práctica: atrapa hasta `KeyboardInterrupt`.
- Excepciones propias: hereda de `Exception` y crea una **base por dominio**, así quien te consume atrapa `AppError` y cubre todo tu módulo.
- `raise NewError("contexto") from exc` conserva la causa en el traceback.
- `raise` solo (sin argumentos) dentro de un `except` re-lanza preservando el traceback original.
- Python 3.11+: `ExceptionGroup` y `except*` para errores simultáneos en concurrencia.

> **Analogía**: los `except` son filtros apilados en un embudo. Si el filtro grueso va arriba, nada llega a los finos.

## 1.5 Diseño orientado a contratos: SOLID, Strategy y Adapter (P5)

El problema: dos formas de obtener lo mismo (scraping HTML vs consumir API REST), y mañana podrían ser tres (RSS, otro medio). El error clásico es meter un `if source == "api"` dentro del servicio.

**La idea central**: el servicio no debe saber *cómo* se obtienen los artículos, solo que *alguien sabe hacerlo*.

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class Article:                       # modelo de dominio común
    external_id: str
    title: str
    url: str
    published_at: datetime
    body: str
    source: str

class ArticleSource(ABC):            # el contrato (puerto)
    @abstractmethod
    def fetch(self, since: datetime | None = None) -> list[Article]: ...

class CnnScraperSource(ArticleSource):   # adaptador 1
    def __init__(self, url, http_client): ...
    def fetch(self, since=None) -> list[Article]: ...   # HTML -> Article

class CnnApiSource(ArticleSource):       # adaptador 2
    def __init__(self, base_url, api_key, http_client): ...
    def fetch(self, since=None) -> list[Article]: ...   # JSON -> Article

class NewsService:                       # depende de la abstracción
    def __init__(self, sources: list[ArticleSource], repo):
        self._sources = sources
        self._repo = repo
    def ingest(self, since=None):
        for source in self._sources:
            self._repo.save_many(source.fetch(since))
```

Cómo se llaman las piezas:
- **Strategy**: `ArticleSource` es la estrategia intercambiable; `NewsService` es el contexto.
- **Adapter**: cada implementación traduce un formato externo (HTML, JSON) al modelo interno `Article`.
- **Factory / registry**: elegir la implementación por configuración, no por `if`.
  ```python
  SOURCES = {"cnn_api": CnnApiSource, "cnn_scraper": CnnScraperSource}
  source = SOURCES[config.source_type](**config.params)
  ```
- **Inyección de dependencias**: el `http_client` entra por constructor → testeable sin red.

SOLID aplicado, uno por uno:

| Principio | Cómo aparece aquí |
|---|---|
| **S**RP | El scraper solo extrae; el repo solo persiste; el servicio solo orquesta |
| **O**CP | Agregar una fuente nueva = crear una clase, **no** modificar `NewsService` |
| **L**SP | Cualquier `ArticleSource` es sustituible: mismo tipo de retorno, mismas excepciones documentadas |
| **I**SP | Contrato mínimo (`fetch`), no un mega-interface con `login`, `parse_html`, `paginate` |
| **D**IP | `NewsService` depende de `ArticleSource` (abstracción), no de `CnnApiSource` (concreto) |

Lo que la clase original (`NewsScrappingService.__init__(url)` + `scrapper()`) hace mal: el nombre acopla el servicio a una técnica de extracción, y `url` en el constructor no aplica a una API con key + paginación. Por eso se sube un nivel de abstracción.

Detalles que suman: normalización de zona horaria, deduplicación por `external_id` o hash de URL, paginación, reintentos con backoff, y un `logger` estructurado por fuente.

> **Analogía**: `ArticleSource` es el enchufe de la pared. Tu casa (el servicio) no sabe si la luz viene de un panel solar o de la hidroeléctrica; solo sabe que ahí hay 127V. Cambiar la generadora no te obliga a recablear la casa.

## 1.6 Estrategia de testing con APIs externas (P6)

### Pirámide

| Nivel | Qué prueba | Velocidad / costo |
|---|---|---|
| Unit | Parsers, mappers, lógica de negocio pura | Miles, milisegundos, gratis |
| Integration | Tu código contra un doble del HTTP, o contra Postgres en contenedor | Decenas de segundos |
| Contract | Que el schema de la API externa sigue siendo el que esperas | Pocos, contra sandbox |
| E2E / smoke | El flujo real, contra la API real | Muy pocos, fuera del CI normal |

### Test doubles, con nombres correctos

- **Stub**: devuelve datos fijos (un JSON de ejemplo).
- **Mock**: además verifica *cómo* se le llamó (`assert_called_once_with`).
- **Fake**: implementación funcional simplificada (un `InMemoryArticleSource`).
- **Spy**: envuelve el real y registra las llamadas.

Gracias al diseño de P5, tus tests de `NewsService` usan un `FakeArticleSource` y **no tocan red en absoluto**.

### Librerías (Python)

`pytest` (+ `pytest-mock`, `pytest-cov`, `pytest-asyncio`), `unittest.mock`, `responses` o `requests-mock` (interceptan `requests`), `respx` (para `httpx`), `vcrpy` / `pytest-recording` (graba y reproduce cassettes), `freezegun` (congelar el tiempo), `factory-boy` (construir objetos de prueba), `hypothesis` (property-based), `testcontainers` (Postgres/Redis reales y efímeros), `jsonschema` o Pydantic (validar contrato de respuesta), `beautifulsoup4` + fixtures HTML guardadas para el scraper.

### La parte que insistían: es una API **real**, ¿de qué hay que estar pendiente?

Esto es lo que querían oír, y va en dos frentes.

**Frente 1 — en los tests**
- **Los tests nunca pegan a la API real.** Tres razones, en este orden: cada llamada **cuesta dinero** y consume cuota; los tests se vuelven **no determinísticos** (la red falla, los datos cambian, el test rojo no significa que tu código esté mal); y son lentos.
- Mockea **en el límite HTTP**, no tu propia lógica. Si mockeas `CnnApiSource.fetch`, no estás probando nada tuyo; intercepta la petición HTTP y deja correr tu parser.
- **VCR / cassettes**: grabas la respuesta real **una vez**, se versiona en el repo y se reproduce siempre. Regla obligatoria: filtrar headers de `Authorization` y API keys antes de commitear el cassette.
- **Smoke tests contra la API real**: un puñado mínimo, marcados `@pytest.mark.live`, deshabilitados por defecto (`addopts = -m "not live"`), corriendo en un cron nocturno con **sandbox key** y presupuesto acotado. Sirven para detectar que la API cambió, no para validar tu lógica.
- **Contract testing**: valida la respuesta contra un JSON Schema. Si la API cambia un campo, falla ahí y no en producción.
- Para el scraper, el equivalente: HTML fixtures guardados + un job canario aparte que descarga la página real y avisa si cambió la estructura.

**Frente 2 — en el código de producción, para no quemar dinero**

Los tests previenen gasto *durante el desarrollo*; el gasto real se controla en el diseño:

- **Caché** con TTL, y HTTP condicional (`ETag` / `If-Modified-Since`) → un 304 normalmente no cuenta o cuesta menos.
- **Rate limiter** propio (token bucket) para no rebasar la cuota del plan.
- **Backoff exponencial con jitter** en reintentos, y **no reintentar 4xx**: un 400/401/404 va a fallar igual las 3 veces; solo gastas dinero.
- **Circuit breaker**: tras N fallos consecutivos, deja de llamar por X minutos.
- **Presupuesto y kill switch**: contador de llamadas por día; si se rebasa, la aplicación se apaga sola y alerta.
- **Fetch incremental**: pedir solo `since=última_ejecución`, con paginación y `limit`, en vez de traer todo cada vez.
- **Deduplicación** antes de llamar: si ya tienes el artículo, no lo vuelvas a pedir.
- **Observabilidad**: métrica de llamadas y de costo estimado, con alerta.

Y estas protecciones **también se testean**, sin gastar un centavo:

```python
def test_no_reintenta_en_400(mocked_http):
    mocked_http.get(URL, status=400)
    with pytest.raises(ClientError):
        source.fetch()
    assert mocked_http.call_count == 1      # no reintentó

def test_usa_cache_en_segunda_llamada(mocked_http):
    mocked_http.get(URL, json=PAYLOAD)
    source.fetch(); source.fetch()
    assert mocked_http.call_count == 1      # la segunda salió de caché
```

> **Analogía**: probar contra la API real es como aprender a manejar practicando en la autopista. El simulador (mocks) es para aprender; sales a la autopista una vez, de noche y con instructor (smoke test nocturno), solo para confirmar que la autopista sigue donde estaba.

## 1.7 Modelado de BD: relaciones N:M y permisos (P7)

Un usuario tiene muchas tareas y una tarea puede estar compartida con muchos usuarios → **relación muchos a muchos**, y en SQL eso siempre se resuelve con una **tabla pivote** (join table).

```sql
CREATE TABLE users (
    id          BIGSERIAL PRIMARY KEY,
    email       CITEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
    id          BIGSERIAL PRIMARY KEY,
    owner_id    BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT 'todo',
    due_date    DATE,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_tasks_owner ON tasks(owner_id);

CREATE TYPE share_role AS ENUM ('viewer', 'editor');

CREATE TABLE task_shares (
    task_id     BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
    user_id     BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role        share_role NOT NULL DEFAULT 'viewer',
    granted_by  BIGINT NOT NULL REFERENCES users(id),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (task_id, user_id)          -- evita compartir dos veces al mismo
);
CREATE INDEX idx_task_shares_user ON task_shares(user_id);   -- "compartidas conmigo"
```

Decisiones que hay que **justificar en voz alta**:

- **PK compuesta `(task_id, user_id)`** en vez de un `id` propio: garantiza unicidad del share sin un `UNIQUE` extra. (Si tu ORM se lleva mal con PKs compuestas, usa `id` + `UNIQUE(task_id, user_id)`.)
- **`owner_id` en `tasks` vs meter `'owner'` en el enum de la pivote**: las dos son defendibles.
  - Con `owner_id`: consultas de propiedad triviales, `NOT NULL` garantiza que toda tarea tenga dueño.
  - Todo en la pivote (`owner`, `editor`, `viewer`): modelo uniforme, permite transferir la propiedad y compartir con varios dueños, pero pierdes la garantía de "exactamente un owner" salvo con un índice parcial único.
  - Respuesta madura: `owner_id` en `tasks` **y** el enum limitado a `viewer`/`editor`. Si luego piden transferencia de propiedad, migras.
- **Índices**: `idx_tasks_owner` para "mis tareas", `idx_task_shares_user` para "compartidas conmigo". Sin el segundo, listar el inbox de un usuario escanea toda la pivote.
- **`ON DELETE CASCADE`**: borrar una tarea borra sus shares. Para el usuario, ojo: quizá prefieras `RESTRICT` o soft delete para no perder historial.
- **Auditoría**: `granted_by` y `created_at` responden "¿quién me compartió esto y cuándo?", que es la primera pregunta de soporte.

Consulta típica: todas las tareas visibles para un usuario, con su rol.

```sql
SELECT t.*, 'owner' AS role
FROM tasks t WHERE t.owner_id = :uid
UNION ALL
SELECT t.*, s.role::text
FROM tasks t JOIN task_shares s ON s.task_id = t.id
WHERE s.user_id = :uid;
```

Cómo escala si piden más (menciónalo como evolución, no lo construyas de entrada):
- Compartir con **equipos**: tabla `teams`, `team_members`, y la pivote acepta `user_id` **o** `team_id` (o dos pivotes separadas).
- Permisos granulares: modelo genérico `permissions(subject_type, subject_id, resource_type, resource_id, action)` — flexible, pero mata la integridad referencial. Solo si de verdad hace falta.
- Enlaces públicos: `share_links(token, task_id, expires_at, role)`.
- Cuidado con **N+1**: al listar tareas con sus colaboradores, un `JOIN` o `selectinload`, nunca un query por tarea.

> **Analogía**: la pivote es la lista de invitados de un evento. La tarea es el evento, el usuario es la persona, y el `role` es qué dice su gafete: organizador, staff o público.

## 1.8 Diseño REST (P8)

Reglas base: los recursos son **sustantivos en plural**, el verbo lo pone HTTP, la jerarquía expresa pertenencia.

```
GET    /api/v1/tasks?status=open&page=1&limit=20   200
POST   /api/v1/tasks                               201 + header Location
GET    /api/v1/tasks/{id}                          200 | 404
PUT    /api/v1/tasks/{id}                          200   (reemplazo total)
PATCH  /api/v1/tasks/{id}                          200   (actualización parcial)
DELETE /api/v1/tasks/{id}                          204

GET    /api/v1/tasks/{id}/shares                   200
POST   /api/v1/tasks/{id}/shares                   201   body: {user_id, role}
PATCH  /api/v1/tasks/{id}/shares/{user_id}         200   body: {role}
DELETE /api/v1/tasks/{id}/shares/{user_id}         204

GET    /api/v1/me/tasks?filter=shared_with_me      200
```

Errores típicos que penalizan: `/getTasks`, `/api/v1/task/create`, usar `POST` para todo, devolver `200` con `{"error": ...}` dentro.

**Status codes**

| Code | Cuándo |
|---|---|
| 200 | OK con cuerpo |
| 201 | Creado (+ `Location`) |
| 204 | OK sin cuerpo (DELETE) |
| 400 | Petición malformada (JSON inválido) |
| 401 | No autenticado (no sé quién eres) |
| 403 | Autenticado pero sin permiso |
| 404 | No existe |
| 409 | Conflicto (ya compartido con ese usuario) |
| 422 | Sintaxis bien, semántica mal (validación de campos) |
| 429 | Rate limit |
| 500 | Error nuestro |

Matiz que gusta: para recursos privados, devolver **404 en vez de 403** evita filtrar que el recurso existe.

**DTOs**: no expongas la entidad de BD. Separa el modelo de dominio del schema de entrada/salida.

```python
class TaskCreateDTO(BaseModel):     # entrada: solo lo que el cliente puede mandar
    title: str
    description: str | None = None
    due_date: date | None = None

class TaskResponseDTO(BaseModel):   # salida: solo lo que el cliente debe ver
    id: int
    title: str
    status: str
    owner: UserSummaryDTO
    my_role: str
```

Por qué: evita **mass assignment** (que alguien mande `owner_id` o `is_admin` en el body), desacopla la API de la BD (puedes refactorizar tablas sin romper clientes) y documenta el contrato solo.

Otros puntos: versionado (`/v1` en la ruta es lo más pragmático), paginación (`limit`/`offset` o cursor), filtrado y orden por query params, formato de error consistente (RFC 7807 `application/problem+json`), idempotencia (`PUT` y `DELETE` lo son; `POST` no, y si hace falta se usa un `Idempotency-Key`).

## 1.9 Autenticación y autorización (P9)

### Cómo funciona un JWT

Tres partes separadas por puntos, cada una en base64url: `header.payload.signature`.

```
header    {"alg": "HS256", "typ": "JWT"}
payload   {"sub": "42", "role": "admin", "iat": 1712, "exp": 1712900, "jti": "..."}
signature HMACSHA256(base64(header) + "." + base64(payload), SECRET)
```

Lo crítico: **el payload no está cifrado, solo firmado**. Cualquiera lo decodifica; nadie puede modificarlo sin invalidar la firma. Por lo tanto: **nunca metas datos sensibles en un JWT**.

Claims estándar: `sub` (sujeto), `exp` (expiración), `iat` (emitido en), `iss` (emisor), `aud` (audiencia), `jti` (id único, sirve para revocar).

`HS256` (secreto compartido, simétrico) vs `RS256` (par de llaves; el backend firma con la privada y cualquier servicio verifica con la pública — mejor para microservicios).

### El flujo backend / frontend

1. `POST /auth/login` con credenciales → backend valida contra el hash (`bcrypt`/`argon2`) y **firma** un access token corto (5–15 min) + un refresh token largo (días).
2. El frontend lo manda en cada request: `Authorization: Bearer <token>`.
3. El backend, en un middleware, **verifica la firma y el `exp`** — sin ir a la BD. Eso es lo *stateless*: el token se valida solo.
4. Cuando expira, el frontend usa el refresh token contra `POST /auth/refresh` y obtiene uno nuevo.

### Dónde se almacena el token

| Lugar | Pro | Contra |
|---|---|---|
| Cookie `HttpOnly; Secure; SameSite=Strict` | JS no puede leerla → inmune a XSS; se manda sola | Necesitas protección CSRF; más fricción cross-domain |
| `localStorage` | Simple, control total desde JS | **Cualquier XSS roba el token**; persiste tras cerrar el navegador |
| Memoria (variable de JS) | No sobrevive a XSS persistente ni a recarga | Se pierde al refrescar; se combina con refresh en cookie |

Respuesta recomendada: **access token en memoria + refresh token en cookie HttpOnly**. Si dan a elegir una sola, cookie HttpOnly.

### Revocación (el hueco del JWT)

Un JWT válido lo es hasta que expira: no hay "logout" real del lado del servidor. Soluciones: tokens de vida corta, **refresh tokens rotativos** guardados en BD (revocables, y si se reusa uno viejo detectas robo), o una **denylist de `jti` en Redis** con TTL = tiempo restante del token.

### Sesiones (la alternativa stateful)

1. Login → el servidor genera un **session id** aleatorio y lo guarda en un store (Redis/BD) junto al `user_id`.
2. Lo manda en cookie `HttpOnly`.
3. En cada request, el servidor **busca la sesión en el store** y carga el usuario.

| | JWT | Sesión |
|---|---|---|
| Estado | Stateless | Stateful (store) |
| Verificación | Firma, sin I/O | Lookup en Redis/BD |
| Revocación | Difícil | Instantánea (borras la sesión) |
| Escala horizontal | Trivial | Requiere store compartido |
| Bueno para | APIs, móvil, microservicios | Apps web monolíticas |

### Roles y buenas prácticas

- **RBAC**: `users` — `user_roles` — `roles` — `role_permissions`. Los roles viven en la BD.
- El rol puede ir como claim para evitar un query, pero **si cambian los permisos el token viejo sigue diciendo el rol viejo** hasta expirar. Por eso: tokens cortos, o consultar la BD en operaciones sensibles.
- Chequeo centralizado, no `if user.role == "admin"` esparcido:
  ```python
  @router.delete("/tasks/{id}")
  def delete(id: int, user = Depends(require_permission("task:delete"))): ...
  ```
- **Permisos, no roles**, cuando crece: `task:read`, `task:delete`. Un rol es un paquete de permisos; así agregar un rol nuevo no toca el código.
- **Autorización a nivel de recurso**, no solo de ruta: que seas `editor` no basta, tienes que ser editor **de esa tarea**. Es la vulnerabilidad más común (IDOR / BOLA, el #1 del OWASP API Top 10).
- Nunca confíes en el frontend: ocultar un botón no es seguridad.
- Menor privilegio por defecto: deniega salvo que haya un permiso explícito.

> **Analogía**: el JWT es un boleto de concierto con holograma — el de la puerta lo valida mirándolo, sin llamar a nadie; pero si te lo roban, sirve hasta que termine el evento. La sesión es una lista de invitados en la entrada: el portero llama a la oficina cada vez, y te pueden tachar de la lista al instante.

## 1.10 Docker, Compose y orquestación (P10)

Cuatro servicios: `tms` (app principal), `email-service`, `postgres`, `redis`.

**Dockerfile multi-stage**, imagen pequeña y sin root:

```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.12-slim
RUN useradd -m appuser
COPY --from=builder /install /usr/local
WORKDIR /app
COPY . .
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn", "-b", "0.0.0.0:8000", "app:app"]
```

**docker-compose.yml**:

```yaml
services:
  tms:
    build: ./tms
    env_file: .env
    environment:
      DATABASE_URL: postgresql://app:${DB_PASSWORD}@db:5432/tms
      REDIS_URL: redis://cache:6379/0
      EMAIL_SERVICE_URL: http://email:8001
    ports: ["8000:8000"]
    depends_on:
      db:    { condition: service_healthy }
      cache: { condition: service_healthy }
    networks: [backend]
    restart: unless-stopped

  email:
    build: ./email-service
    environment:
      REDIS_URL: redis://cache:6379/1
    depends_on:
      cache: { condition: service_healthy }
    networks: [backend]          # sin 'ports': no se expone al exterior

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: tms
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - pgdata:/var/lib/postgresql/data          # named volume: persistencia
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro   # bind mount RO
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d tms"]
      interval: 5s
      retries: 5
    networks: [backend]

  cache:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redisdata:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 5
    networks: [backend]

volumes:
  pgdata:
  redisdata:

networks:
  backend:
    driver: bridge
```

**Lo que preguntaron explícitamente:**

*Volumes* — el filesystem de un contenedor es efímero: si lo recreas, pierdes los datos. Tres tipos:
- **Named volume** (`pgdata:/var/lib/postgresql/data`): Docker lo gestiona, es el correcto para bases de datos.
- **Bind mount** (`./src:/app`): mapea una carpeta del host; ideal para hot-reload en desarrollo, mala idea en producción. Añade `:ro` para solo lectura.
- **tmpfs**: en RAM, para datos sensibles y efímeros.

*Networks* — Compose crea una red por defecto donde todos los servicios se ven **por nombre de servicio**: la app se conecta a `db:5432`, no a `localhost` ni a una IP. Ese DNS interno es lo que hace todo esto funcionar. Definir redes explícitas permite **segmentar**: por ejemplo `frontend` (tms + un nginx) y `backend` (tms + email + db + cache), de modo que nada exterior alcance la BD. Y clave: **si un servicio no lleva `ports:`, no es accesible desde el host** — solo desde la red interna. La BD nunca debería publicar el 5432 en producción.

*Otros puntos*: `depends_on` sin `condition` solo espera a que el contenedor **arranque**, no a que esté **listo**; por eso los `healthcheck`. Secretos vía `.env` o Docker secrets, nunca hardcodeados ni en la imagen. `restart: unless-stopped`. Un `docker-compose.override.yml` para dev.

**Cuándo pasar a Kubernetes**: Compose es un solo host, sin autoescalado ni self-healing entre nodos. K8s te da `Deployment` (réplicas + rolling updates), `Service` (descubrimiento y balanceo), `Ingress` (entrada HTTP), `ConfigMap`/`Secret` (configuración), `PVC` (almacenamiento), `HPA` (autoescalado), `StatefulSet` (para Postgres, aunque casi siempre conviene usar una BD gestionada en vez de correrla en el clúster).

> **Analogía**: el Dockerfile es la receta, la imagen es el platillo empaquetado y el contenedor es el platillo servido. Compose es el mesero que sirve cuatro platillos coordinados en la misma mesa; Kubernetes es el gerente de una cadena de restaurantes que abre sucursales solo, reemplaza cocineros que se enferman y ajusta el personal según la fila en la puerta.

## 1.11 El mismo stack en la nube (P11)

La respuesta correcta no es "todo en Kubernetes", es **mapear cada pieza al servicio gestionado que corresponde** y justificar el nivel de control que se cede.

| Pieza | AWS | Azure | GCP |
|---|---|---|---|
| App TMS | ECS Fargate / EKS / App Runner | Container Apps / AKS | Cloud Run / GKE |
| Email service | Lambda o ECS + **SQS** | Functions + Service Bus | Cloud Functions + Pub/Sub |
| Postgres | **RDS / Aurora** | Azure DB for PostgreSQL | Cloud SQL |
| Redis | **ElastiCache** | Azure Cache for Redis | Memorystore |
| Registry de imágenes | ECR | ACR | Artifact Registry |
| Entrada / TLS | ALB + ACM | App Gateway | Cloud Load Balancing |
| Envío de correo | SES | Comm. Services | SendGrid |
| Secretos | Secrets Manager / SSM | Key Vault | Secret Manager |
| Logs y métricas | CloudWatch | Monitor | Cloud Monitoring |
| Archivos | S3 | Blob Storage | GCS |

Los argumentos que hay que dar:

- **Por qué gestionado**: backups automáticos, parches, Multi-AZ, réplicas de lectura y failover que no vas a implementar mejor tú mismo. Correr Postgres en un pod es asumir el trabajo de un DBA.
- **Desacoplar el email service con una cola** (SQS/Pub-Sub) en vez de llamada HTTP directa: si el proveedor de correo se cae, los mensajes esperan en la cola en vez de perderse; puedes reintentar, y una **DLQ** captura los que fallan siempre. Además la app responde rápido porque no espera el envío.
- **Sin servidores que administrar**: Fargate/Cloud Run evitan gestionar nodos. EKS/GKE solo si ya tienes varios equipos y necesitas el ecosistema K8s.
- **Red**: VPC con subnets públicas (solo el load balancer) y privadas (apps, RDS, ElastiCache). Security groups como firewall: la BD solo acepta tráfico del security group de la app. Es exactamente la misma idea que las `networks` de Compose, un nivel arriba.
- **Escalado**: autoscaling por CPU/memoria o por profundidad de la cola.
- **IaC**: Terraform (o CDK/Bicep). Nada se crea a mano en la consola; el entorno debe ser reproducible y revisable en un PR.
- **CI/CD**: build de imagen → push a ECR → despliegue con rolling update o blue/green.
- **Costo**: mencionarlo demuestra madurez — Fargate cuesta más por hora pero elimina trabajo de operación; empezar con instancias pequeñas y escalar por métricas.

## 1.12 Uso de AI en el trabajo (P12)

No hay respuesta "correcta"; evalúan criterio. Estructura útil: **dónde sí / dónde con cuidado / dónde no**, con ejemplos concretos.

**Dónde aporta más**
- Boilerplate y andamiaje: DTOs, migraciones, configuraciones, parsers.
- Tests: generar casos borde que no se te habían ocurrido, y tests para código legacy sin cobertura.
- Refactors mecánicos y repetitivos a lo largo de muchos archivos.
- Explorar una librería o API desconocida más rápido que leyendo toda la doc.
- Documentación, docstrings, mensajes de commit, descripciones de PR.
- Primer pase de revisión de código y análisis de logs o stack traces.
- Rubber-ducking: explicar un diseño en voz alta y recibir contraargumentos.

**Dónde con cuidado**
- **Nunca pegar código propietario, credenciales o PII** en herramientas no aprobadas por la empresa.
- Código de seguridad y criptografía: revisión humana obligatoria.
- **Dependencias alucinadas**: verificar que el paquete que sugiere existe de verdad (hay ataques de *slopsquatting* que registran esos nombres inventados).
- Decisiones de arquitectura: el modelo no conoce el contexto del negocio, la deuda técnica ni las restricciones del equipo.

**Los principios que quieren oír**
- **Tú eres responsable del código que mergeas**, lo haya escrito quien lo haya escrito. Si no lo entiendes, no va.
- Los **tests son la red de seguridad** que hace seguro aceptar código generado.
- Prompts con contexto: pegar el código real, las convenciones del equipo y el error exacto, en vez de pedir en abstracto.
- Es un multiplicador de un desarrollador senior y una muleta peligrosa para uno junior: acelera lo que ya sabes revisar.
- Menciona herramientas concretas que uses (Claude Code, Copilot, Cursor) y un caso real donde te ahorró tiempo — y uno donde te dio algo mal y lo detectaste.

---

# 2. Las preguntas de la entrevista, con su respuesta

En cada una: **lo que te preguntaron** (tal como quedó registrado) y **cómo responderla**.

## P1 — Promedio de temperatura por ciudad

> **Lo que se preguntó**
> "From a list of tuples containing the info of a city and temperature, return the average temperature for each city."
> Entrada: `[(city1, n), (city2, n), (city2, n), (city4, n), (city1, n), (city5, n), (city3, n)...]`
> Salida: `city1 value, city2 value, city3 value...`

```python
from collections import defaultdict

def average_by_city(readings):
    sums, counts = defaultdict(float), defaultdict(int)
    for city, temp in readings:
        sums[city] += temp
        counts[city] += 1
    return {city: round(sums[city] / counts[city], 2) for city in sums}
```

Qué decir mientras lo escribes: una sola pasada, **O(n) tiempo / O(k) memoria**; `defaultdict` evita el `if key not in dict`; si pidieran mediana o percentiles guardaría la lista completa; el dict conserva el orden de primera aparición desde Python 3.7.

## P2 — ¿Qué imprime `d.my_method()`?

> **Lo que se preguntó**
> "Qué imprimirá el método al final." Te dieron este código (con errores a propósito):
> ```python
> import abc import abc, abstractmethod
>
> class A (ABC):
>     abstractmethod
>     def my_method():
>         print("A")
> class B(A)
>     def my_method():
>         print("B")
> class C(A)
>     def my_method():
>         print("C")
> class D(B,C)
>     ...
>
> d = D()
> d.my_method()   # ¿qué imprimirá?
> ```
> Y hubo énfasis extra en **llamar al constructor y a `super()` cuando heredamos**.

**Respuesta: imprime `B`**, porque `D.__mro__` es `(D, B, C, A, ABC, object)` y `B` aparece antes que `C`.

Los gotchas del código tal como estaba escrito — esto es lo que buscaban que detectaras:

1. `import abc import abc, abstractmethod` no es sintaxis válida → debe ser `from abc import ABC, abstractmethod`.
2. `abstractmethod` **sin `@`** no decora nada: es solo una expresión suelta, así que `A` no sería abstracta y podrías instanciarla sin implementar nada.
3. `def my_method():` **sin `self`** → `TypeError: my_method() takes 0 positional arguments but 1 was given` al llamarlo desde la instancia.
4. Faltan los `:` en `class B(A)`, `class C(A)` y `class D(B,C)`.

Versión corregida:

```python
from abc import ABC, abstractmethod

class A(ABC):
    @abstractmethod
    def my_method(self): ...

class B(A):
    def my_method(self): print("B")

class C(A):
    def my_method(self): print("C")

class D(B, C): pass

D().my_method()      # B
print(D.__mro__)     # (D, B, C, A, ABC, object)
```

Sobre constructores y `super()`: en herencia múltiple hay que usar `super().__init__(**kwargs)` en toda la cadena, no `A.__init__(self)`, para que el MRO recorra todas las ramas exactamente una vez. Ver 1.2.

## P3 — Pre/post proceso sin modificar el método

> **Lo que se preguntó**
> ```python
> class D():
>     def my_method(self):
>         # can't modify this method
>         print("D")
>
> d = D()
> d.my_method()   # before -> 'preproces' and after -> 'postprocess'
> ```
> Salida esperada: `'preproc'` / `D` / `'postproc'`.
> "How can you achieve this behaviour with Python?"

```python
import functools

def with_hooks(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print("preproc")
        result = func(*args, **kwargs)
        print("postproc")
        return result
    return wrapper

D.my_method = with_hooks(D.my_method)   # monkey patch: no tocamos la clase

d = D()
d.my_method()      # preproc / D / postproc
```

Nombra también las alternativas (te da puntos): subclase con `super()`, decorador de clase que envuelve todos los métodos, `__getattribute__` para interceptar cualquier atributo, o un context manager si el pre/post pertenece al bloque y no al método. Y menciona `functools.wraps` explícitamente.

## P4 — Manejar errores por tipo

> **Lo que se preguntó**
> Misma clase de P3:
> ```python
> d = D()
> d.my_method()   # Error1 -> e1 and Error2 -> e2 and any other -> any
> ```
> "How can you handle errors by their type or class? How to achieve handling by different type of errors?"

```python
try:
    d.my_method()
except Error1 as exc:
    handle_e1(exc)
except (Error2, Error3) as exc:   # tupla: varios tipos, mismo manejo
    handle_e2(exc)
except Exception as exc:          # fallback genérico, siempre al final
    handle_any(exc)
else:
    print("sin errores")
finally:
    cleanup()
```

Y uniéndolo con P3, que es lo que se hace en producción:

```python
def handle_errors(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Error1:
            return "e1"
        except Error2:
            return "e2"
        except Exception:
            return "any"
    return wrapper
```

Lo que quieren oír: **específico antes que genérico** (el match es por `isinstance`, gana el primero), tupla para agrupar, `as exc` para inspeccionar, `finally` para liberar recursos, jerarquía propia con una base por dominio, `raise ... from exc` para conservar la causa, y `raise` pelado para re-lanzar sin perder el traceback.

## P5 — Diseño para soportar scraping y API

> **Lo que se preguntó**
> Parte de diseño, no de implementación.
> `CNN -> release -> API -> extract articles`. Dos formas: **Scraping** (implementado por nosotros) y **API** (consumida).
> "What would be your design to support both extraction ways?"
> El entrevistador te dio esta clase de partida:
> ```python
> class NewsScrappingService:
>     def __init__(self, url):
>         self.url = url
>     def scrapper(self):   # Extract articles cnn.com
> ```
> Tú respondiste con interfaces y contratos.

Tu respuesta iba bien encaminada; lo que hay que hacer es **estructurarla y nombrar los patrones**:

1. Define un **modelo de dominio común**: `Article` (dataclass). Todo termina ahí, venga de HTML o de JSON.
2. Define el **contrato**: `ArticleSource(ABC)` con un solo método, `fetch(since) -> list[Article]`.
3. Dos **adaptadores**: `CnnScraperSource` y `CnnApiSource`. Cada uno sabe hablar su formato y traducirlo a `Article`.
4. `NewsService` recibe las fuentes **por constructor** (inyección de dependencias) y no sabe nada de HTML ni de HTTP.
5. Una **factory/registry** elige la implementación según configuración, para que no haya un `if source == "api"` en la lógica.

Los patrones: **Strategy** (fuentes intercambiables) + **Adapter** (traducción de formato) + **Factory**. Los principios: **OCP** (agregar una fuente es crear una clase, no modificar el servicio) y **DIP** (el servicio depende de la abstracción). El código completo está en 1.5.

Crítica explícita a la clase dada: `NewsScrappingService` acopla el servicio a una técnica en su propio nombre, y `url` en el constructor no modela una API con key, paginación y rate limit. Hay que subir un nivel de abstracción.

## P6 — Estrategia de testing (y no gastar dinero)

> **Lo que se preguntó**
> Sobre la P5:
> - ¿Qué estrategia de testing usarías?
> - ¿Qué librerías de Python?
> - "Este servicio llama a una API, una API **real**, ¿necesitas hacer algo específico? ¿necesitamos estar atentos de algo en específico?" — insistiendo en que estas llamadas **cuestan dinero**, y en que debe haber una manera, en la lógica y con los tests, de prevenir gastar de más.

Respuesta en tres capas:

**1. Estrategia.** Pirámide: muchos unit tests del parser y de la lógica de negocio; unos cuantos de integración contra un doble del HTTP; contract tests para el schema de la API; un puñado de smoke tests reales fuera del CI. Gracias al diseño de P5, `NewsService` se testea con un `FakeArticleSource` en memoria, sin red.

**2. Librerías.** `pytest` + `pytest-mock` + `pytest-cov`, `unittest.mock`, `responses`/`requests-mock` (o `respx` para httpx), `vcrpy`/`pytest-recording` para cassettes, `freezegun`, `factory-boy`, `hypothesis`, `testcontainers` para Postgres real y efímero, `jsonschema` o Pydantic para validar el contrato, `beautifulsoup4` con fixtures HTML guardadas.

**3. Lo específico de que la API sea real** — esto es lo que insistían:

- **Los tests nunca llaman a la API real.** Razones, en este orden: cada llamada **cuesta dinero** y consume cuota; los tests dejan de ser **determinísticos** (rojo por red caída ≠ tu código está mal); y son lentos.
- Mockear **en el límite HTTP**, no tu propia lógica: si mockeas `CnnApiSource.fetch` no pruebas nada tuyo.
- **VCR**: grabar la respuesta real una vez, versionar el cassette, reproducir siempre — filtrando `Authorization` y API keys antes de commitear.
- **Smoke tests reales**, mínimos, marcados `@pytest.mark.live`, apagados por defecto (`addopts = -m "not live"`), en un cron nocturno con **sandbox key** y presupuesto acotado. Sirven para detectar que la API cambió, no para validar tu lógica.
- Y sobre todo: **la prevención del gasto se diseña en el código de producción**, no solo en los tests — caché con TTL y `ETag`/`If-Modified-Since`, rate limiter, backoff exponencial con jitter, **no reintentar 4xx** (un 400 falla igual las 3 veces y solo gastas), circuit breaker, fetch incremental con `since` en vez de traer todo, deduplicación, cuota diaria con kill switch, y métricas de llamadas con alerta de costo.
- **Esas protecciones también se testean, gratis**: `assert mocked_http.call_count == 1` después de dos llamadas comprueba que la caché funcionó; un test con status 400 comprueba que no reintentaste. Detalle completo en 1.6.

## P7 — Schema de BD para compartir tareas

> **Lo que se preguntó**
> Nivel base de datos. Tablas: `User` y `Task`. `User -> CRUD -> Tasks`.
> Nueva feature: **task sharing**.
> ```
> user1 -> creates -> task1
> user1 -> shares  -> task1 -> user2
> user2 -> read    -> task1
> ```
> "What would be the schema/db that supports this behaviour?"
> Tú respondiste con una tabla pivote `usersTask` con un campo rol tipo enum (`owner`, `editor`, `guest`).

**Tu respuesta era correcta.** Es exactamente el patrón esperado: la relación pasa de 1:N a **N:M**, y eso obliga a una tabla pivote con el rol como atributo de la relación.

Para blindarla, añade lo que le faltaba:
- **PK compuesta** `(task_id, user_id)` → evita compartir dos veces con la misma persona.
- **Índice en `user_id`** → sin él, "tareas compartidas conmigo" escanea toda la pivote.
- `granted_by` y `created_at` → auditoría de quién compartió y cuándo.
- `ON DELETE CASCADE` en las FKs.
- Sobre `owner` dentro del enum: defendible, pero es más limpio mantener `owner_id NOT NULL` en `tasks` (garantiza un único dueño) y dejar el enum en `viewer`/`editor`. Si te lo cuestionan, el argumento a favor de meter `owner` en la pivote es que permite **transferir la propiedad** y tener un modelo uniforme.

El DDL completo y las consultas están en 1.7.

## P8 — Diseño de endpoints REST

> **Lo que se preguntó**
> Cuál sería tu diseño de endpoints siguiendo REST.
> Tú respondiste dibujando las rutas en papel, con sus HTTP status codes, el nombre de los recursos, el método HTTP a enviar, y explicaste un poco de DTOs.

Ese es el enfoque correcto. Lo que hay que asegurarse de cubrir siempre:

- Recursos como **sustantivos en plural**; el verbo lo pone HTTP. Nada de `/getTasks` ni `/tasks/create`.
- La jerarquía expresa pertenencia: `/tasks/{id}/shares/{user_id}`.
- `POST` devuelve **201 + header `Location`**; `DELETE` devuelve **204** sin cuerpo.
- Distinguir **401** (no sé quién eres) de **403** (sé quién eres, no puedes) de **404**; y **409** para conflicto, **422** para validación semántica, **429** para rate limit.
- Para recursos privados, devolver 404 en vez de 403 evita filtrar que existen.
- **DTOs**: schema de entrada separado del de salida y ambos separados de la entidad de BD. Previene mass assignment y desacopla la API del esquema.
- Extras que rematan: versionado `/api/v1`, paginación, filtros por query params, formato de error consistente (RFC 7807), idempotencia de `PUT`/`DELETE`.

Tabla de rutas completa en 1.8.

## P9 — Autenticación

> **Lo que se preguntó**
> - ¿Cómo la implementarías?
> - ¿Cómo funciona JWT? ¿Cómo funciona JWT respecto al backend y al frontend? ¿Dónde se almacena y dónde se chequea el token?
> - ¿Cómo se verifica la sesión cuando la auth es mediante sesión?
> - ¿Cómo se chequean los roles y cuál sería una buena práctica?

Respuestas en corto (desarrollo completo en 1.9):

- **Qué es un JWT**: `header.payload.signature` en base64url. Firmado, **no cifrado** → cualquiera lee el payload, nadie lo altera sin romper la firma. Nunca metas datos sensibles.
- **Backend**: en el login valida credenciales contra el hash (bcrypt/argon2) y **firma** el token. En cada request, un middleware **verifica firma y `exp` sin tocar la BD** — eso es lo stateless.
- **Frontend**: lo envía en `Authorization: Bearer <token>`.
- **Dónde se almacena**: cookie `HttpOnly; Secure; SameSite` (inmune a XSS, necesita anti-CSRF) es lo recomendable; `localStorage` es cómodo pero cualquier XSS te roba el token. Lo mejor: access token en memoria + refresh token en cookie HttpOnly.
- **Revocación**: el hueco del JWT. Se resuelve con tokens cortos (5–15 min), refresh tokens rotativos guardados en BD, o denylist de `jti` en Redis.
- **Sesión**: el servidor genera un session id aleatorio, lo guarda en un store (Redis/BD) y lo manda en cookie `HttpOnly`. En cada request **busca la sesión en el store** → stateful, con revocación instantánea, pero requiere store compartido para escalar horizontalmente.
- **Roles**: RBAC con los roles en BD; chequeo centralizado en un middleware/dependency (`require_permission("task:delete")`), no `if role == "admin"` disperso. Mejor **permisos que roles** cuando crece. Y lo más importante: **autorización a nivel de recurso**, no solo de ruta — ser `editor` no basta, tienes que ser editor **de esa tarea** (IDOR/BOLA es el #1 del OWASP API Top 10). Nunca confiar en el frontend; denegar por defecto.

## P10 — Docker, orquestación y Kubernetes

> **Lo que se preguntó**
> "¿Cómo orquestarías un Dockerfile y un compose en algo como esto?"
> `app1 -> tms`, `app2 -> email service`, `db -> pg`, `cache -> redis`.
> También preguntó específicamente sobre el **volume** y el **network** que van dentro del YAML.

Estructura de la respuesta: un Dockerfile **multi-stage** por app (imagen chica, usuario no root, healthcheck) y un `docker-compose.yml` con los cuatro servicios. YAML completo en 1.10.

Lo que preguntaron explícitamente:

- **Volumes**: el filesystem del contenedor es efímero; si lo recreas, pierdes los datos. **Named volume** (`pgdata:/var/lib/postgresql/data`) para la BD — Docker lo gestiona y sobrevive a `docker compose down`. **Bind mount** (`./src:/app`) para hot-reload en desarrollo, con `:ro` cuando solo se lee; mala idea en producción. **tmpfs** para datos sensibles en RAM.
- **Networks**: Compose crea una red donde los servicios se resuelven **por nombre de servicio** — la app conecta a `db:5432`, no a `localhost`. Ese DNS interno es lo que hace que todo funcione. Definir redes explícitas permite **segmentar** (`frontend` vs `backend`) y, sobre todo: **un servicio sin `ports:` no es accesible desde el host**, solo desde la red interna. Postgres nunca debe publicar el 5432 en producción.
- Añade: `healthcheck` + `depends_on: {condition: service_healthy}`, porque `depends_on` a secas solo espera a que el contenedor **arranque**, no a que esté **listo**. Secretos por `.env` o Docker secrets, nunca en la imagen.
- **Kubernetes**: Compose es un solo host, sin autoescalado ni self-healing. K8s aporta `Deployment` (réplicas, rolling updates), `Service`, `Ingress`, `ConfigMap`/`Secret`, `PVC`, `HPA`, `StatefulSet`. Matiz que suma: para Postgres, en producción casi siempre conviene una BD gestionada en vez de un StatefulSet en el clúster.

## P11 — Lo mismo, con servicios cloud

> **Lo que se preguntó**
> Cómo harías lo de la pregunta 10, pero usando servicios cloud.

No respondas "todo en Kubernetes". Responde **mapeando cada pieza al servicio gestionado** y justificando:

- TMS y email service → **ECS Fargate** (o Cloud Run / Container Apps); EKS/GKE solo si ya hay ecosistema K8s.
- Postgres → **RDS/Aurora**: backups, parches, Multi-AZ, réplicas de lectura y failover que no vas a hacer mejor a mano.
- Redis → **ElastiCache**.
- El email service se **desacopla con una cola** (SQS/Pub-Sub) en vez de HTTP directo: si el proveedor de correo cae, los mensajes esperan; hay reintentos y **DLQ**; y la app responde sin esperar el envío. Envío con SES.
- Imágenes en **ECR**, entrada por **ALB + ACM** (TLS), secretos en **Secrets Manager**, logs y métricas en **CloudWatch**, archivos en **S3**.
- **Red**: VPC con subnets públicas (solo el balanceador) y privadas (apps, RDS, ElastiCache); security groups como firewall. Es la misma idea que las `networks` de Compose, un nivel arriba.
- **IaC con Terraform** — nada se crea a mano en la consola — y CI/CD que construye la imagen, la sube y despliega con rolling o blue/green.
- Cierra con **costo**: Fargate cuesta más por hora pero elimina operación; empezar chico y escalar por métricas o por profundidad de cola.

Tabla de equivalencias AWS/Azure/GCP en 1.11.

## P12 — ¿Cómo usarías AI en tu trabajo?

> **Lo que se preguntó**
> "¿Cómo usarías AI en tu trabajo?"

Estructura: **dónde sí / dónde con cuidado / qué principio te guía**, con ejemplos tuyos.

- **Sí**: boilerplate y andamiaje, generación de tests y casos borde, refactors mecánicos, explorar librerías nuevas, documentación y descripciones de PR, primer pase de code review, análisis de logs y stack traces, rubber-ducking de diseño.
- **Con cuidado**: nunca pegar código propietario, credenciales o PII en herramientas no aprobadas; revisión humana obligatoria en seguridad y cripto; verificar que las dependencias sugeridas **existen** (dependencias alucinadas / slopsquatting); las decisiones de arquitectura son tuyas porque el modelo no conoce el negocio ni la deuda técnica.
- **El principio**: eres responsable del código que mergeas, lo haya escrito quien lo haya escrito; si no lo entiendes, no entra. Los tests son la red de seguridad que hace seguro aceptar código generado.
- Cierra con un ejemplo concreto tuyo — una vez que te ahorró horas, y una vez que te dio algo mal y lo detectaste. Eso último es lo que demuestra criterio.

---

# 3. Ejercicios nuevos

Resuélvelos sin mirar la sección 4. Los marcados con 💬 son de explicar en voz alta, como en la entrevista.

## Bloque A — Python core / OOP

**E1.** Misma lista de tuplas de P1, pero ahora devuelve por ciudad `(promedio, mínimo, máximo, número de lecturas)`. ¿Cambia tu elección entre "guardar la lista" y "guardar acumuladores"?

**E2.** ¿Qué imprime y por qué?

```python
class A:
    def who(self): print("A")
class B(A):
    def who(self): print("B"); super().who()
class C(A):
    def who(self): print("C"); super().who()
class D(B, C):
    def who(self): print("D"); super().who()

D().who()
```

**E3.** ¿Por qué esto lanza `TypeError` y cómo lo arreglas sin cambiar el orden `(C, B)`?

```python
class X(B, C): pass
class Y(C, B): pass
class Z(X, Y): pass
```

**E4.** Escribe un decorador `retry(times=3, exceptions=(ConnectionError,))` que reintente la función y, si agota los intentos, re-lance la última excepción conservando el traceback. Añádele backoff.

**E5.** Tienes `class Repo` con 6 métodos. Escribe un **decorador de clase** que loguee entrada y salida de todos los métodos públicos (los que no empiezan con `_`) sin tocar el código de `Repo`.

**E6.** ¿Qué devuelve `f()`? Explica la interacción entre `finally` y `return`.

```python
def f():
    try:
        return "try"
    finally:
        return "finally"
```

**E7.** Define una jerarquía de excepciones para un cliente HTTP: errores de red, errores 4xx y errores 5xx. Escribe el `try/except` que reintente solo en red y 5xx, y falle rápido en 4xx.

## Bloque B — Diseño y testing

**E8.** Añade una tercera fuente al diseño de P5: un **feed RSS**. ¿Qué archivos tocas y cuáles **no**? Si tu respuesta incluye modificar `NewsService`, algo está mal en el diseño.

**E9.** 💬 La API de CNN empieza a exigir paginación con cursor, pero el scraper no la necesita. ¿Cómo lo modelas sin filtrar el detalle de la API hacia `NewsService`?

**E10.** Escribe los tests para `CnnApiSource.fetch()` usando `responses`, cubriendo: (a) el happy path parsea 2 artículos, (b) un 500 se reintenta 3 veces, (c) un 401 **no** se reintenta, (d) llamar dos veces con la caché caliente hace **una sola** petición HTTP.

**E11.** 💬 Tu jefe dice: "los tests con mocks no prueban nada real, hagamos que peguen a la API de verdad". Da tres argumentos concretos en contra y una propuesta que le dé lo que quiere sin quemar presupuesto.

## Bloque C — Datos, API y auth

**E12.** Escribe la consulta SQL que devuelve, para un usuario, todas las tareas que puede **editar** (las suyas y las compartidas con rol `editor`), ordenadas por `due_date`, paginadas de 20 en 20. ¿Qué índices necesita?

**E13.** Diseña los endpoints para: revocar un share, listar quién tiene acceso a una tarea, y que un usuario abandone una tarea compartida con él. Método, ruta, código de éxito y códigos de error de cada uno.

**E14.** 💬 Un usuario con rol `viewer` sobre `task1` hace `PATCH /api/v1/tasks/1` y funciona. ¿Dónde estuvo el fallo y en qué capa se arregla? ¿Qué código HTTP debería haber devuelto?

**E15.** El equipo quiere logout inmediato con JWT. Diseña la solución completa: qué guardas, dónde, con qué TTL, y qué pasa con el refresh token. ¿Qué has sacrificado del modelo stateless?

## Bloque D — Infra y cierre

**E16.** En el compose de P10, el `email-service` necesita leer plantillas de correo desde una carpeta del host que el equipo edita a diario, y guardar un log de envíos que debe sobrevivir a `docker compose down`. Escribe la sección `volumes` del servicio y justifica cada tipo.

**E17.** 💬 Quieres que Postgres **no** sea alcanzable desde tu máquina pero sí desde `tms`, y que un `nginx` sea el único expuesto al exterior. Define las `networks` y qué servicio va en cuál.

**E18.** 💬 Traduce el compose completo a AWS. Para cada uno de los 4 servicios di qué servicio gestionado usarías y **por qué no** el más obvio en al menos un caso.

---

# 4. Soluciones

**E1.** Con min/max/count basta acumular 4 escalares por ciudad en una sola pasada; sigue siendo O(1) de memoria por ciudad. Solo necesitarías la lista completa si pidieran mediana, percentiles o desviación estándar.

```python
stats = {}
for city, t in data:
    s = stats.setdefault(city, {"sum": 0.0, "n": 0, "min": t, "max": t})
    s["sum"] += t; s["n"] += 1
    s["min"] = min(s["min"], t); s["max"] = max(s["max"], t)
result = {c: (s["sum"]/s["n"], s["min"], s["max"], s["n"]) for c, s in stats.items()}
```

**E2.** Imprime `D`, `B`, `C`, `A`. El MRO es `(D, B, C, A, object)` y cada `super()` salta al **siguiente del MRO**, no al padre directo: por eso `B.who` acaba llamando a `C.who`, aunque `C` no sea padre de `B`. Es el ejemplo canónico de `super()` cooperativo — y la razón de que `super()` sea confuso si lo lees como "mi padre".

**E3.** `TypeError: Cannot create a consistent method resolution order (MRO) for bases X, Y`. `X` impone B→C y `Y` impone C→B; C3 no puede satisfacer ambas restricciones a la vez. Arreglos: que `Z` herede de una sola, eliminar una de las dos jerarquías, o —la solución real— extraer el comportamiento común a un **mixin** y componer en vez de heredar de ambas combinaciones.

**E4.**

```python
import functools, time

def retry(times=3, exceptions=(ConnectionError,), delay=0.5):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, times + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions:
                    if attempt == times:
                        raise                       # conserva el traceback
                    time.sleep(delay * 2 ** (attempt - 1))   # backoff exponencial
        return wrapper
    return decorator
```

En producción, añade **jitter** (`+ random.uniform(0, 0.3)`) para que N clientes no reintenten sincronizados.

**E5.**

```python
import functools, inspect

def _logged(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"-> {func.__name__}")
        result = func(*args, **kwargs)
        print(f"<- {func.__name__}")
        return result
    return wrapper

def log_methods(cls):
    for name, attr in list(vars(cls).items()):
        if name.startswith("_") or not inspect.isfunction(attr):
            continue
        setattr(cls, name, _logged(attr))
    return cls
```

Uso: `@log_methods` encima de la clase, o `Repo = log_methods(Repo)` si no puedes tocarla. Ojo: `vars(cls)` solo ve los métodos definidos **en esa clase**, no los heredados.

**E6.** Devuelve `"finally"`. Un `return` (o `break`) dentro de `finally` **descarta** el valor del `try` y además se tragaría una excepción pendiente. Por eso es un antipatrón: `finally` limpia, no decide el resultado.

**E7.**

```python
class HttpError(Exception): ...
class NetworkError(HttpError): ...    # timeout, DNS, conexión
class ClientError(HttpError): ...     # 4xx
class ServerError(HttpError): ...     # 5xx

try:
    call()
except (NetworkError, ServerError):
    retry_with_backoff()   # transitorios
except ClientError:
    raise                  # nuestro request está mal: reintentar no lo arregla
```

Idea clave: **reintenta solo lo transitorio**. Un 400/401/404 fallará igual las tres veces y solo gastas tiempo y dinero — conecta directo con P6.

**E8.** Creas **un solo archivo nuevo**: `RssSource(ArticleSource)` con su `fetch()` que parsea el feed y devuelve `Article`. Registras la clase en el diccionario de la factory y añades su configuración. **No tocas** `NewsService`, ni `Article`, ni las fuentes existentes, ni sus tests. Eso *es* el Open/Closed Principle en la práctica: si tuvieras que abrir `NewsService` para añadir un `elif`, el diseño falló.

**E9.** La paginación es un **detalle de implementación de esa fuente**, así que vive dentro de `CnnApiSource.fetch()`: el método pagina internamente en un bucle (o devuelve un generador) y entrega la lista/stream completo. El contrato `fetch(since) -> Iterable[Article]` no cambia. Si necesitas streaming para no cargar todo en memoria, cambia el tipo de retorno a `Iterator[Article]` **en la interfaz** — eso sí es un cambio de contrato legítimo, y el scraper simplemente hará `yield` de una sola página. Lo que nunca debe pasar es que `NewsService` reciba o pase un `cursor`.

**E10.**

```python
import pytest, responses

URL = "https://api.cnn.com/v1/articles"

@responses.activate
def test_happy_path(source):
    responses.get(URL, json={"articles": [A1, A2]}, status=200)
    articles = source.fetch()
    assert len(articles) == 2
    assert articles[0].title == "..."          # se probó el parser, no el mock

@responses.activate
def test_reintenta_en_500(source):
    responses.get(URL, status=500)
    responses.get(URL, status=500)
    responses.get(URL, json={"articles": []}, status=200)
    source.fetch()
    assert len(responses.calls) == 3

@responses.activate
def test_no_reintenta_en_401(source):
    responses.get(URL, status=401)
    with pytest.raises(ClientError):
        source.fetch()
    assert len(responses.calls) == 1           # ni un centavo de más

@responses.activate
def test_segunda_llamada_usa_cache(source):
    responses.get(URL, json={"articles": [A1]}, status=200)
    source.fetch(); source.fetch()
    assert len(responses.calls) == 1
```

Nota los dos últimos: son tests **del control de gasto**, y no cuestan nada.

**E11.** Tres argumentos:
1. **Determinismo**: un test que falla por la red caída o porque hoy CNN publicó otra cosa deja de ser señal; el equipo empieza a ignorar el rojo y el CI pierde su valor.
2. **Costo y cuota**: cada push de cada dev multiplica las llamadas; puedes consumir la cuota mensual en una tarde de trabajo, o rebasar el rate limit y romper producción.
3. **Cobertura de casos borde**: con la API real no puedes provocar un 500, un timeout o un JSON malformado cuando quieras; con mocks sí, y esos son justo los caminos que más se rompen.

Propuesta que le da lo que quiere: **contract tests** contra el sandbox más un **smoke test nocturno** mínimo contra la API real, con presupuesto acotado y alerta a Slack. Detecta el cambio de contrato en menos de 24h sin meter la red en el CI de cada PR.

**E12.**

```sql
SELECT t.*
FROM tasks t
WHERE t.owner_id = :uid
   OR EXISTS (
        SELECT 1 FROM task_shares s
        WHERE s.task_id = t.id AND s.user_id = :uid AND s.role = 'editor'
      )
ORDER BY t.due_date NULLS LAST, t.id
LIMIT 20 OFFSET :offset;
```

Índices: `tasks(owner_id)`, `task_shares(user_id, role)` — o `(user_id) INCLUDE (role)` —, y `tasks(due_date, id)` para el orden. Nota: para tablas grandes, la **paginación por cursor** (`WHERE (due_date, id) > (:last_due, :last_id)`) escala mucho mejor que `OFFSET`, que se degrada linealmente. Y `ORDER BY` debe incluir un desempate (`id`) o la paginación puede repetir o saltarse filas.

**E13.**

```
GET    /api/v1/tasks/{id}/shares               200 | 401 403 404
DELETE /api/v1/tasks/{id}/shares/{user_id}     204 | 401 403 404      (el owner revoca)
DELETE /api/v1/tasks/{id}/shares/me            204 | 401 404          (yo abandono)
```

Detalles que suman: `.../shares/me` es un alias legible para "el usuario autenticado" y evita que alguien borre el share de otro por descuido; revocar un share inexistente puede devolver 404 o 204 (idempotente) — ambas son defendibles si eres consistente; y el owner no puede eliminar su propia propiedad por esta ruta, para eso sería una transferencia (`PATCH /tasks/{id}` con `owner_id`).

**E14.** El fallo es de **autorización a nivel de recurso**. Casi seguro el middleware validó que el usuario está autenticado y quizá que tiene "acceso a la tarea", pero no comparó su **rol sobre esa tarea concreta** con la acción solicitada. Se arregla en la capa de autorización/servicio, no en el controlador y **jamás** en el frontend: antes de mutar, se resuelve el rol efectivo del usuario sobre ese recurso y se exige `owner` o `editor`. Debía devolver **403** (o 404 si prefieres no revelar que la tarea existe). Esto es IDOR/BOLA, el riesgo #1 del OWASP API Security Top 10.

**E15.** Solución: **denylist de `jti` en Redis**. En el logout, insertas el `jti` del access token con `TTL = exp - now`, y el middleware consulta la denylist antes de aceptar el token. Como los access tokens son cortos (5–15 min), la denylist se mantiene diminuta y se autolimpia sola por TTL. El refresh token se **borra o marca como revocado en la BD**, que es lo que realmente cierra la sesión: sin él no se pueden emitir nuevos access tokens. Añade rotación de refresh tokens y detección de reuso (si llega un refresh ya usado, revocas toda la familia: es señal de robo).

Lo sacrificado: la validación deja de ser puramente stateless — ahora hay un lookup a Redis por request. En la práctica es un GET de microsegundos, mucho más barato que una sesión en BD, y el trade-off vale la pena. Alternativa sin Redis: bajar el `exp` a 5 minutos y aceptar que el logout tarda hasta 5 minutos en surtir efecto.

**E16.**

```yaml
  email:
    volumes:
      - ./templates:/app/templates:ro   # bind mount RO: el equipo edita en el host
      - maillogs:/app/logs              # named volume: sobrevive a `down`
volumes:
  maillogs:
```

Justificación: el **bind mount** conecta con el filesystem del host, así que los cambios en las plantillas se ven sin reconstruir la imagen; va en `:ro` porque el contenedor solo lee y así evitas que un bug sobrescriba el fuente. El **named volume** lo gestiona Docker, es independiente del ciclo de vida del contenedor y persiste tras `docker compose down` (solo `down -v` lo borra). Matiz de producción: los logs de una app normalmente van a stdout y los recoge el driver de logging, no a un volumen — el volumen es aceptable si es un log de negocio auditable.

**E17.**

```yaml
networks:
  frontend:   # nginx + tms
  backend:    # tms + email + db + cache
```
- `nginx`: redes `[frontend]`, **con** `ports: ["80:80", "443:443"]` — el único expuesto.
- `tms`: redes `[frontend, backend]`, **sin** `ports`. Es el puente: recibe de nginx, habla con la BD.
- `email`, `db`, `cache`: redes `[backend]`, **sin** `ports`.

La clave: quitar `ports:` de Postgres es lo que lo vuelve inalcanzable desde tu máquina; mientras esté en `backend`, `tms` lo sigue resolviendo como `db:5432`. Segmentar además impide que `nginx` alcance la BD si lo comprometen.

**E18.** Mapeo: `tms` → ECS Fargate detrás de un ALB; `email-service` → Lambda o un worker de ECS consumiendo **SQS**; `db` → RDS PostgreSQL Multi-AZ; `cache` → ElastiCache Redis.

El "por qué no el más obvio", que es lo que evalúan:
- **Por qué no EKS** aunque venías de contenedores: EKS te cobra el control plane y te obliga a operar el clúster; con dos servicios no hay nada que justifique esa carga. Fargate da contenedores sin nodos que parchear. EKS entra cuando hay muchos equipos y necesitas el ecosistema.
- **Por qué no Postgres en un contenedor de ECS**: perderías backups automáticos, failover, Multi-AZ y parches. Correr tu propia BD es asumir un rol de DBA a cambio de ahorrar poco.
- **Por qué no una llamada HTTP directa al email service**: la cola desacopla, absorbe picos, reintenta sola, aísla la caída del proveedor de correo y te da DLQ. La app responde sin esperar el envío.

---

# 5. Checklist de repaso

Marca solo lo que puedas explicar **en voz alta y sin mirar**. Lo que quede vacío es tu tema débil.

**Python / OOP**
- [ ] Escribo una agregación con `defaultdict` sin pensarlo y digo su complejidad
- [ ] Calculo un MRO a mano y explico el diamante
- [ ] Sé que `super()` es "el siguiente del MRO", no "el padre"
- [ ] Escribo un decorador con `functools.wraps` de memoria
- [ ] Conozco 3 formas de añadir comportamiento sin tocar el original
- [ ] Ordeno `except` de específico a genérico y sé qué hacen `else` y `finally`
- [ ] Diseño una jerarquía de excepciones con base por dominio

**Diseño y testing**
- [ ] Explico los 5 principios SOLID con un ejemplo del mismo sistema
- [ ] Distingo Strategy, Adapter y Factory y digo dónde encaja cada uno
- [ ] Explico la diferencia entre stub, mock, fake y spy
- [ ] Argumento por qué los tests no llaman a la API real (3 razones)
- [ ] Enumero 5 mecanismos de producción para no quemar cuota de API
- [ ] Sé qué es un cassette de VCR y qué hay que filtrar antes de commitearlo

**Datos, API y auth**
- [ ] Modelo un N:M con pivote, PK compuesta e índices, y justifico cada uno
- [ ] Distingo 401 / 403 / 404 / 409 / 422 y sé cuándo devolver 404 en vez de 403
- [ ] Explico qué es un DTO y qué ataque previene
- [ ] Describo un JWT parte por parte y por qué no lleva datos sensibles
- [ ] Comparo JWT vs sesión en 4 ejes y digo cuándo usar cada uno
- [ ] Explico dónde guardar el token y el trade-off XSS/CSRF
- [ ] Explico por qué el chequeo de rol por ruta no basta (IDOR/BOLA)

**Infra**
- [ ] Escribo un Dockerfile multi-stage con usuario no root
- [ ] Explico named volume vs bind mount vs tmpfs
- [ ] Explico el DNS interno de Compose y qué significa no poner `ports:`
- [ ] Sé por qué `depends_on` sin healthcheck no basta
- [ ] Mapeo un compose a servicios gestionados de AWS y justifico el "por qué no"
- [ ] Explico por qué desacoplar con una cola en vez de HTTP directo

**Cierre**
- [ ] Tengo lista una respuesta de AI con un caso donde ayudó y uno donde falló
