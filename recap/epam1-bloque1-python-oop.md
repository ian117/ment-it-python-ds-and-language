# Bloque 1 — Python Core / OOP (Preguntas 1–4)

Guía autosuficiente para repasar. Orden: temas → explicación → preguntas de la entrevista con respuesta → ejercicios nuevos → soluciones.

---

## 0. Mapa de temas y preguntas

| # | Pregunta de la entrevista | Temas que evalúa |
|---|---|---|
| P1 | Promedio de temperatura por ciudad desde una lista de tuplas | Agrupación/agregación, `defaultdict`, `Counter`, `statistics.mean`, complejidad |
| P2 | ¿Qué imprime `d.my_method()` con herencia múltiple? | MRO / C3, diamante, `ABC` + `@abstractmethod`, `super()` cooperativo, sintaxis de `import` |
| P3 | Añadir pre/post proceso a un método que no puedes modificar | Decoradores, `functools.wraps`, monkey patching, herencia, context managers, `__getattribute__` |
| P4 | Manejar Error1 → e1, Error2 → e2, cualquier otro → any | Jerarquía de excepciones, orden de `except`, tuplas, `else`/`finally`, excepciones custom |

---

## 1. Explicación de los temas

### 1.1 Agregación de datos (P1)

El patrón es siempre el mismo: **recorrer una vez, acumular en un diccionario, reducir al final**.

Tres formas de acumular:

```python
from collections import defaultdict
from statistics import mean

data = [("mx", 30), ("ny", 10), ("mx", 20)]

# A) Guardar todos los valores (más memoria, más flexible)
buckets = defaultdict(list)
for city, temp in data:
    buckets[city].append(temp)
result = {city: mean(temps) for city, temps in buckets.items()}

# B) Acumular suma y conteo (O(1) de memoria por ciudad) <- la que prefieren
sums, counts = defaultdict(float), defaultdict(int)
for city, temp in data:
    sums[city] += temp
    counts[city] += 1
result = {city: sums[city] / counts[city] for city in sums}
```

Puntos que suman en la entrevista:
- **Complejidad**: O(n) tiempo, O(k) memoria (k = ciudades únicas). Ordenar y agrupar con `itertools.groupby` sería O(n log n) → peor.
- `defaultdict` vs `dict.setdefault()` vs `dict.get(key, 0)`: los tres valen, `defaultdict` es el idiomático.
- `Counter` **no** sirve aquí: cuenta ocurrencias, no promedia. Sirve para el `counts` si quieres.
- Casos borde: lista vacía, ciudad con un solo dato, división por cero (imposible si construyes el dict al vuelo), redondeo (`round(x, 2)`) y **normalizar la clave** (`city.strip().lower()`).
- `mean([])` lanza `StatisticsError`.

> **Analogía**: es como contar propinas por mesero. No necesitas guardar cada billete (opción A); basta llevar un papelito por mesero con "total acumulado / número de propinas" (opción B).

---

### 1.2 MRO y herencia múltiple (P2)

Cuando llamas `d.my_method()`, Python busca el atributo recorriendo una lista lineal de clases: el **MRO** (Method Resolution Order), calculado con el algoritmo **C3 linearization**.

Reglas de C3, en corto:
1. La clase misma va primero.
2. Se respeta el orden de declaración de las bases (izquierda a derecha).
3. Una clase nunca aparece antes que sus subclases.

```python
class D(B, C): ...
D.__mro__  # (D, B, C, A, ABC, object)
```

Como `B` va antes que `C`, gana `B`. **El problema del diamante** (A en la punta, B y C en medio, D abajo) se resuelve así: A aparece **una sola vez**, al final.

`super()` **no significa "mi clase padre"**, significa "la siguiente clase en el MRO del objeto real". Por eso en herencia múltiple todas las clases deben llamar a `super().__init__(...)`, si no, ramas enteras del árbol se quedan sin inicializar.

```python
class A:
    def __init__(self, **kw): super().__init__(**kw)   # cooperativo
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

- `ABC` es azúcar sintáctica de `metaclass=ABCMeta`.
- Instanciar una clase con métodos abstractos sin implementar → `TypeError: Can't instantiate abstract class`.
- El chequeo es **en tiempo de instanciación**, no de definición.

> **Analogía**: el MRO es la lista de a quién le preguntas cuando no sabes algo: primero a ti, luego a tu hermano mayor (B), luego al de en medio (C), luego a papá (A). `super()` es "pásale la pregunta al siguiente de la lista", no "pregúntale a papá directo".

---

### 1.3 Decoradores y envolver comportamiento (P3)

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

Si **no puedes tocar** el código de la clase, tienes varias vías:

| Técnica | Cómo | Cuándo |
|---|---|---|
| Monkey patching | `D.my_method = with_hooks(D.my_method)` | No puedes tocar la clase ni crear subclase (afecta a **todas** las instancias) |
| Decorar la instancia | `d.my_method = with_hooks(d.my_method)` | Solo esa instancia |
| Subclase | `class E(D): def my_method(self): print("pre"); super().my_method(); print("post")` | La forma limpia si puedes cambiar quién instancia |
| Decorador de clase | `@decorate_all` sobre la clase, reasigna sus métodos | Muchos métodos a la vez |
| `__getattribute__` / proxy | Interceptas cualquier acceso a atributo | Genérico, potente, difícil de depurar |
| Context manager | `with hooks(): d.my_method()` | El pre/post es del *bloque*, no del método |

`functools.wraps` importa: sin él, `wrapper.__name__` es `"wrapper"` y se rompen introspección, docs y algunos frameworks.

> **Analogía**: el decorador es papel de regalo. El objeto de dentro no cambia; solo lo que ves al recibirlo y al abrirlo. `functools.wraps` es pegarle la etiqueta original al paquete para que se siga sabiendo qué hay dentro.

---

### 1.4 Manejo de excepciones por tipo (P4)

Jerarquía: `BaseException` → `Exception` → todo lo demás (`ValueError`, `KeyError`, `TypeError`, `OSError`…). `KeyboardInterrupt` y `SystemExit` cuelgan de `BaseException`, **no** de `Exception`: por eso `except Exception` no las atrapa (y está bien así).

```python
try:
    d.my_method()
except Error1 as exc:          # más específico primero
    handle_e1(exc)
except (Error2, Error3) as exc: # varios tipos, mismo manejo
    handle_e2(exc)
except Exception as exc:        # fallback
    handle_any(exc)
else:
    print("no hubo error")      # solo si el try no lanzó
finally:
    cleanup()                   # siempre, haya error o no
```

Reglas que preguntan:
- **El orden importa**: Python toma el primer `except` cuyo tipo haga match por `isinstance`. Si pones `except Exception` arriba, los de abajo son código muerto.
- `except:` desnudo (sin tipo) es mala práctica: atrapa `KeyboardInterrupt` incluido.
- Excepciones propias: heredar de `Exception`, crear una base por dominio.
  ```python
  class AppError(Exception): ...
  class NotFound(AppError): ...
  ```
  Así quien te consume puede atrapar `AppError` y cubrir todo tu módulo.
- `raise NewError("contexto") from exc` conserva la causa original en el traceback.
- Re-lanzar: `raise` solo (sin argumentos) dentro de un `except` preserva el traceback original.
- Python 3.11+: `ExceptionGroup` y `except*` para varios errores simultáneos (concurrencia).
- Combinado con P3: un decorador de manejo de errores es el patrón real en producción.

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

> **Analogía**: los `except` son los filtros de un embudo apilado. Si el filtro grueso (`Exception`) va arriba, nada llega a los finos de abajo.

---

## 2. Preguntas de la entrevista, con respuesta

### P1 — Promedio de temperatura por ciudad

```python
from collections import defaultdict

def average_by_city(readings):
    sums, counts = defaultdict(float), defaultdict(int)
    for city, temp in readings:
        sums[city] += temp
        counts[city] += 1
    return {city: round(sums[city] / counts[city], 2) for city in sums}
```

Qué decir en voz alta: una sola pasada, O(n) tiempo / O(k) memoria; `defaultdict` evita el `if key not in dict`; si necesitara mediana o desviación guardaría la lista completa; el orden de salida en Python 3.7+ es el de primera aparición.

### P2 — ¿Qué imprime `d.my_method()`?

**Imprime `B`.** Porque `D.__mro__` es `(D, B, C, A, ABC, object)` y `B` está antes que `C`.

Los gotchas del código tal como venía escrito (esto es lo que buscaban):

1. `import abc import abc, abstractmethod` no es sintaxis válida → debe ser `from abc import ABC, abstractmethod`.
2. `abstractmethod` sin `@` no decora nada: es solo una referencia suelta, así que `A` **no** sería abstracta y podrías instanciarla.
3. `def my_method():` sin `self` → `TypeError: my_method() takes 0 positional arguments but 1 was given` al llamarlo desde la instancia.
4. Faltan los `:` en `class B(A)`, `class C(A)`, `class D(B,C)`.

Bonus que mencionaste (constructores): en herencia múltiple hay que usar `super().__init__(**kwargs)` en toda la cadena, no `A.__init__(self)`, para que el MRO recorra todas las ramas una sola vez.

### P3 — Pre/post proceso sin modificar el método

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

D.my_method = with_hooks(D.my_method)   # monkey patch

d = D()
d.my_method()   # preproc / D / postproc
```

Alternativas que vale la pena nombrar: subclase con `super()`, decorador de clase, `__getattribute__`, o un context manager si el pre/post es del bloque y no del método.

### P4 — Manejo por tipo de error

Ver el bloque `try/except/else/finally` y el decorador `handle_errors` de la sección 1.4. Lo que quieren oír: **específico antes que genérico**, tupla para agrupar tipos, `as exc` para inspeccionar, `finally` para liberar recursos, excepciones propias con una base común, y `raise ... from` para no perder la causa.

---

## 3. Ejercicios nuevos

Resuélvelos sin mirar la sección 4.

**E1.** Misma lista de tuplas, pero ahora devuelve por ciudad: `(promedio, mínimo, máximo, número de lecturas)`. ¿Cambia tu elección entre "guardar lista" y "guardar sumas"?

**E2.** ¿Qué imprime este código y por qué?

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

**E4.** Escribe un decorador `retry(times=3, exceptions=(ConnectionError,))` que reintente la función y, si agota los intentos, re-lance la última excepción conservando el traceback.

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

---

## 4. Soluciones

**E1.** Con min/max/count basta con acumular 4 escalares por ciudad (`sum`, `count`, `min`, `max`) en una sola pasada; sigue siendo O(1) de memoria por ciudad. Solo necesitarías la lista completa si pidieran mediana, percentiles o desviación estándar exacta en una pasada.

```python
stats = {}
for city, t in data:
    s = stats.setdefault(city, {"sum": 0, "n": 0, "min": t, "max": t})
    s["sum"] += t; s["n"] += 1
    s["min"] = min(s["min"], t); s["max"] = max(s["max"], t)
```

**E2.** Imprime `D`, `B`, `C`, `A`. El MRO es `(D, B, C, A, object)` y cada `super()` salta al **siguiente del MRO**, no al padre directo: por eso `B.who` termina llamando a `C.who`, aunque `C` no sea padre de `B`. Es el ejemplo canónico de `super()` cooperativo.

**E3.** `TypeError: Cannot create a consistent method resolution order (MRO) for bases X, Y`. `X` fija el orden B→C y `Y` fija C→B; C3 no puede linearizar ambas restricciones a la vez. Arreglos: eliminar una de las dos jerarquías, hacer que `Z` herede solo de una, o extraer el comportamiento común a un mixin en vez de heredar de las dos combinaciones.

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
                        raise            # 'raise' pelado conserva el traceback
                    time.sleep(delay * attempt)   # backoff
        return wrapper
    return decorator
```

**E5.**

```python
import functools, inspect

def log_methods(cls):
    for name, attr in list(vars(cls).items()):
        if name.startswith("_") or not inspect.isfunction(attr):
            continue
        setattr(cls, name, _logged(attr))
    return cls

def _logged(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"-> {func.__name__}")
        result = func(*args, **kwargs)
        print(f"<- {func.__name__}")
        return result
    return wrapper
```

Uso: `Repo = log_methods(Repo)` si no puedes poner `@log_methods` encima de la clase.

**E6.** Devuelve `"finally"`. Un `return` (o `break`) dentro de `finally` **descarta** el valor de retorno del `try` y también se tragaría una excepción pendiente. Por eso es un antipatrón: `finally` debe limpiar, no decidir el resultado.

**E7.**

```python
class HttpError(Exception): ...
class NetworkError(HttpError): ...       # timeout, DNS, conexión
class ClientError(HttpError): ...        # 4xx
class ServerError(HttpError): ...        # 5xx

try:
    call()
except (NetworkError, ServerError):
    retry()          # transitorios: reintentar con backoff
except ClientError:
    raise            # nuestro request está mal: reintentar no arregla nada
```

La clave conceptual: **reintenta solo lo transitorio**. Un 400/401/404 va a fallar igual las 3 veces y solo gastas tiempo (y, si es una API de pago, dinero — esto reaparece en la P6).

---

## 5. Checklist de repaso rápido

- [ ] Sé escribir agregación con `defaultdict` sin pensarlo y decir su complejidad
- [ ] Puedo calcular un MRO a mano y explicar el diamante
- [ ] Sé que `super()` = siguiente en el MRO, no "el padre"
- [ ] Escribo un decorador con `functools.wraps` de memoria
- [ ] Conozco 3 formas de añadir comportamiento sin tocar el original
- [ ] Ordeno `except` de específico a genérico y sé qué hace `else`/`finally`
- [ ] Diseño jerarquías de excepciones con una base por dominio
