"""
=============================================================
P4 — Manejar errores por tipo
=============================================================
Misma clase de P3:

    d = D()
    d.my_method()   # Error1 -> e1 and Error2 -> e2 and any other -> any

"How can you handle errors by their type or class?
 How to achieve handling by different type of errors?"

TU TAREA
  1. Escribe el try/except que mapee Error1 -> "e1",
     Error2 -> "e2", cualquier otro -> "any".
  2. ¿Por qué el ORDEN de los except importa? ¿Qué pasa si pones
     `except Exception` arriba?
  3. ¿Qué hacen `else` y `finally`? ¿Cuándo corre cada uno?
  4. ¿Por qué `except Exception` NO atrapa Ctrl+C?
  5. Uniéndolo con P3: conviértelo en un DECORADOR que envuelva
     cualquier función con este manejo de errores.

BONUS (E7 de la guía): diseña la jerarquía de excepciones de un
cliente HTTP (red, 4xx, 5xx) y escribe el try/except que reintenta
solo en red y 5xx, y falla rápido en 4xx. ¿Por qué esa distinción
ahorra dinero?
"""


class Error1(Exception): ...
class Error2(Exception): ...


class D:
    def my_method(self, fail=None):
        if fail == 1:
            raise Error1("boom 1")
        if fail == 2:
            raise Error2("boom 2")
        if fail == 3:
            raise ValueError("otro")
        print("D")


# --- 1. Tu try/except:


# --- 2. Orden de los except:


# --- 3. else / finally:


# --- 4. Ctrl+C:


# --- 5. Como decorador:


if __name__ == "__main__":
    d = D()
