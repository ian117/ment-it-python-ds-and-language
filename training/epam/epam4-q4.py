"""
=============================================================
P4 — Manejar errores por tipo  ·  RESUELTO
=============================================================
Misma clase de P3:

    d = D()
    d.my_method()   # Error1 -> e1 and Error2 -> e2 and any other -> any

"How can you handle errors by their type or class?
 How to achieve handling by different type of errors?"
"""

import functools


# =============================================================
# Jerarquía de excepciones
# =============================================================
# Regla: crea SIEMPRE una base por dominio. Así quien te consume
# puede atrapar AppError y cubrir todo tu módulo de una, sin
# enumerar cada excepción concreta.

class AppError(Exception):
    """Base de dominio. Todo lo nuestro hereda de aquí."""


class Error1(AppError): ...
class Error2(AppError): ...


class D:
    def my_method(self, fail=None):
        # El método LANZA. No captura sus propios errores:
        # quien llama es quien decide qué hacer.
        if fail == 1:
            raise Error1("boom 1")
        if fail == 2:
            raise Error2("boom 2")
        if fail == 3:
            raise ValueError("otro")
        print("D")


# =============================================================
# 1. El try/except
# =============================================================
# Va en el CALL SITE, no dentro del método.
# El try envuelve LO MÍNIMO que puede fallar: si metes 5 líneas
# dentro, cuando salte el except no sabes cuál de las 5 lo causó.

def demo(d, fail):
    try:
        d.my_method(fail)            # <- solo lo que puede fallar
    except Error1 as exc:            # más específico primero
        print(f"e1  ({exc})")
    except Error2 as exc:            # tupla si varios comparten manejo:
        print(f"e2  ({exc})")        #   except (Error2, Error3) as exc:
    except Exception as exc:         # fallback, SIEMPRE al final
        print(f"any ({type(exc).__name__}: {exc})")
    else:
        print("sin errores")         # solo si el try NO lanzó
    finally:
        print("cleanup")             # siempre, haya o no error


# =============================================================
# 2. ¿Por qué importa el orden de los except?
# =============================================================
# El match es por isinstance() y gana EL PRIMERO que haga match,
# no el más específico. Python no busca "el mejor candidato":
# recorre los except de arriba a abajo y se detiene en el primero
# que cuadre.
#
# Por eso, si pones `except Exception` arriba, todo lo demás es
# CÓDIGO MUERTO: nunca se ejecuta, y Python no te avisa.
#
#   MAL                          BIEN
#   except Exception: ...        except Error1: ...
#   except Error1: ...  # muerto except Exception: ...
#
# Regla: de específico a genérico, siempre.


# =============================================================
# 3. else / finally
# =============================================================
#   try     -> el código que puede fallar
#   except  -> qué hacer si falló
#   else    -> corre SOLO si el try terminó sin excepción.
#              ¿Para qué existe si podría ir al final del try?
#              Para no envolver de más: lo que va en else NO está
#              protegido por los except, así que si el else lanza
#              un Error1, no lo atrapa este bloque. Deja claro qué
#              estás vigilando y qué no.
#   finally -> corre SIEMPRE: con error, sin error, con return, e
#              incluso si la excepción se propaga hacia arriba.
#              Es para liberar recursos (cerrar archivos, conexiones).
#
# TRAMPA CLÁSICA (E6 de la guía): ¿qué devuelve esto?
#
#   def f():
#       try:    return "try"
#       finally: return "finally"
#
#   -> "finally". Un return dentro de finally DESCARTA el valor del
#      try y además se tragaría una excepción pendiente. Antipatrón:
#      finally limpia, no decide el resultado.


# =============================================================
# 4. ¿Por qué `except Exception` NO atrapa Ctrl+C?
# =============================================================
# Por la jerarquía. Ctrl+C lanza KeyboardInterrupt, que NO hereda
# de Exception: cuelga directo de BaseException.
#
#   BaseException
#   ├── KeyboardInterrupt   <- Ctrl+C
#   ├── SystemExit          <- sys.exit()
#   ├── GeneratorExit
#   └── Exception           <- `except Exception` atrapa de aquí p/abajo
#       ├── ValueError
#       ├── KeyError
#       ├── OSError
#       └── AppError (la nuestra)
#
# Y eso es INTENCIONAL Y DESEABLE: si `except Exception` atrapara
# el Ctrl+C, no podrías matar un proceso colgado.
#
# Corolario: `except:` desnudo es mala práctica porque equivale a
# `except BaseException` y sí se traga el Ctrl+C. Nunca lo uses.
#
# Si necesitas capturar KeyboardInterrupt (para hacer cleanup),
# re-lánzalo después:
#
#   except KeyboardInterrupt:
#       guardar_estado()
#       raise            # <- devuélvele el control al usuario


# =============================================================
# 5. El mismo manejo, como decorador (une P3 con P4)
# =============================================================

def handle_errors(func):
    @functools.wraps(func)               # conserva __name__, __doc__, firma
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


# Monkey patch: añadimos el manejo sin tocar el código de D.
# OJO: parchear D afecta a TODAS sus instancias, así que aquí lo
# aplicamos sobre una subclase para no romper la demo de arriba.
# En la entrevista, la respuesta es `D.my_method = handle_errors(D.my_method)`.

class DSafe(D):
    pass

DSafe.my_method = handle_errors(D.my_method)


# =============================================================
# BONUS (E7) — Jerarquía de un cliente HTTP
# =============================================================

class HttpError(Exception): ...
class NetworkError(HttpError): ...   # timeout, DNS, conexión rota
class ClientError(HttpError): ...    # 4xx: la culpa es nuestra
class ServerError(HttpError): ...    # 5xx: la culpa es de ellos


def llamar_api(call, retry_with_backoff):
    try:
        return call()
    except (NetworkError, ServerError):
        # TRANSITORIOS: el mismo request puede funcionar en 1 segundo.
        return retry_with_backoff()
    except ClientError:
        # PERMANENTES: un 400/401/404 va a fallar igual las 3 veces.
        # Reintentar solo quema tiempo, cuota y DINERO.
        raise            # `raise` pelado: re-lanza conservando el traceback


# ¿Por qué esta distinción ahorra dinero? Conecta directo con P6:
# reintentar un 4xx multiplica por 3 el costo de una llamada que
# está condenada a fallar. Solo se reintenta lo transitorio.
#
# Y se testea gratis:
#   mocked_http.get(URL, status=400)
#   with pytest.raises(ClientError): source.fetch()
#   assert mocked_http.call_count == 1     # no reintentó


# =============================================================
# Extras que dan puntos en la entrevista
# =============================================================
# - `raise NuevoError("contexto") from exc`
#       encadena la causa: el traceback muestra las dos. Sin el
#       `from`, ocultas el error original y depurar se vuelve ciego.
#
# - `raise` a secas dentro de un except
#       re-lanza preservando el traceback original. Es lo que usas
#       para loguear y dejar que el error siga subiendo.
#       (`raise exc` lo re-lanza pero trunca parte del traceback.)
#
# - Excepciones propias con base por dominio (AppError arriba).
#
# - Python 3.11+: ExceptionGroup y `except*` para varios errores
#       simultáneos en código concurrente (asyncio.TaskGroup).
#
# - No uses excepciones para flujo de control normal, pero sí para
#       lo excepcional: en Python es "más fácil pedir perdón que
#       permiso" (EAFP) y es idiomático.


if __name__ == "__main__":
    d = D()

    print("--- try/except en el call site ---")
    for fail in (None, 1, 2, 3):
        print(f"\nfail={fail}")
        demo(d, fail)

    print("\n--- versión decorada (devuelve en vez de imprimir) ---")
    safe = DSafe()
    for fail in (None, 1, 2, 3):
        print(f"fail={fail} -> {safe.my_method(fail)!r}")
