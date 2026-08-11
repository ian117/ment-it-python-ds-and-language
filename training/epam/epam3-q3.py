"""
=============================================================
P3 — Pre/post proceso sin modificar el método  ·  RESUELTO
=============================================================
Lo que te dieron:

    class D():
        def my_method(self):
            # can't modify this method
            print("D")

    d = D()
    d.my_method()   # before -> 'preproc' and after -> 'postproc'

Salida esperada:  preproc / D / postproc

"How can you achieve this behaviour with Python?"

LA IDEA DE FONDO
    Un decorador es una función que recibe una función y devuelve
    OTRA que la envuelve. El objeto de dentro no cambia; solo lo
    que pasa al entrar y al salir.
    (Analogía: papel de regalo. functools.wraps es pegarle la
     etiqueta original al paquete.)
"""

import contextlib
import functools
import inspect


class D:
    def my_method(self):
        # no puedes modificar este método
        print("D")


# =============================================================
# 1. LA SOLUCIÓN — el decorador + monkey patching
# =============================================================

def with_hooks(func):
    @functools.wraps(func)                 # ver punto 3
    def wrapper(*args, **kwargs):          # *args/**kwargs: firma agnóstica
        print("preproc")
        result = func(*args, **kwargs)     # NO olvides devolver el resultado
        print("postproc")
        return result
    return wrapper


# Monkey patch: reasignamos el atributo de la CLASE.
# Nunca tocamos el cuerpo de my_method.
#
#   D.my_method es una función normal (no está "bound"), así que
#   wrapper recibe la instancia como args[0] y se la pasa intacta.
#
# D.my_method = with_hooks(D.my_method)      <- la respuesta en la pizarra
#
# Aquí lo aplicamos sobre subclases para que las 4 variantes
# convivan en un mismo archivo sin pisarse.


# =============================================================
# 2. LAS OTRAS TÉCNICAS
# =============================================================
# Nombrarlas da puntos: demuestra que elegiste una, no que solo
# conocías una.

# --- (a) Decorar en la CLASE: afecta a todas las instancias -----
class DPatched(D):
    pass

DPatched.my_method = with_hooks(D.my_method)
# Cuándo: no puedes tocar el código fuente y quieres el hook en
# todo el sistema. Peligro: es acción a distancia — otro módulo se
# encuentra un comportamiento que no pidió y no ve de dónde sale.


# --- (b) Decorar la INSTANCIA: solo ese objeto ------------------
def patch_instance(obj):
    # obj.my_method ya viene "bound": self está fijado, por eso
    # wrapper no lo recibe. El atributo vive en obj.__dict__ y
    # tapa al de la clase.
    obj.my_method = with_hooks(obj.my_method)
    return obj
# Cuándo: quieres instrumentar un objeto concreto sin afectar al
# resto. Es la variante quirúrgica.


# --- (c) SUBCLASE: la forma limpia -----------------------------
class DSub(D):
    def my_method(self):
        print("preproc")
        result = super().my_method()
        print("postproc")
        return result
# Cuándo: controlas quién instancia. Es explícito, se lee solo y
# no hay magia. Si puedes elegir, esta gana.
# No sirve si el objeto te lo entrega una librería ya construido.


# --- (d) DECORADOR DE CLASE: muchos métodos de golpe -----------
def decorate_all(cls):
    for name, attr in list(vars(cls).items()):
        if name.startswith("_") or not inspect.isfunction(attr):
            continue
        setattr(cls, name, with_hooks(attr))
    return cls
# Cuándo: logging/timing en los 6 métodos públicos de un Repo.
# OJO: vars(cls) solo ve los métodos definidos EN esa clase, no
# los heredados.

@decorate_all
class Repo:
    def get(self, id): return f"get({id})"
    def save(self, x): return f"save({x})"
    def _internal(self): return "privado, no decorado"


# --- (e) __getattribute__ / proxy: interceptar TODO -------------
class DProxy(D):
    def __getattribute__(self, name):
        attr = super().__getattribute__(name)
        if callable(attr) and not name.startswith("_"):
            return with_hooks(attr)
        return attr
# Cuándo: genérico y potente (así funcionan muchos ORMs y mocks).
# Contra: se dispara en CADA acceso a atributo, cuesta rendimiento
# y es muy fácil provocar recursión infinita. Difícil de depurar.


# --- (f) CONTEXT MANAGER: el pre/post es del BLOQUE ------------
@contextlib.contextmanager
def hooks():
    print("preproc")
    try:
        yield
    finally:
        print("postproc")   # finally: se imprime aunque el bloque falle
# Cuándo: el pre/post pertenece al bloque, no al método.
# Es la opción honesta si lo que quieres es "abrir y cerrar algo"
# alrededor de una llamada puntual, no cambiar el método.


# =============================================================
# 3. ¿QUÉ HACE functools.wraps Y QUÉ SE ROMPE SIN ÉL?
# =============================================================
# El wrapper es una función NUEVA. Sin wraps, hereda su propia
# identidad y la original desaparece:
#
#   __name__      -> "wrapper"   (en vez de "my_method")
#   __doc__       -> None        (el docstring se pierde)
#   __module__, __qualname__, __annotations__ -> los del wrapper
#
# wraps copia todo eso del original al wrapper, y además deja una
# referencia en wrapper.__wrapped__ para poder llegar al de dentro.
#
# Qué se rompe si lo omites:
#   - help() y las docs autogeneradas muestran "wrapper" sin doc.
#   - Los tracebacks y los logs dicen "wrapper", no el método real:
#     depurar se vuelve un infierno cuando tienes 20 funciones
#     decoradas y todas se llaman igual.
#   - inspect.signature() devuelve (*args, **kwargs) en vez de la
#     firma real.
#   - Frameworks que usan introspección se rompen de verdad, no
#     solo cosméticamente: FastAPI y pytest leen la firma para
#     inyectar dependencias y fixtures; Django y Flask usan
#     __name__ para registrar rutas -> dos vistas decoradas
#     colisionan porque ambas se llaman "wrapper".
#
# Es una línea. Ponla siempre.


# =============================================================
# 4. ¿INSTANCIA O TODAS LAS INSTANCIAS?
# =============================================================
# Depende de DÓNDE reasignes, y esto sale de cómo Python busca
# atributos: primero en obj.__dict__, después en el MRO de la clase.
#
#   D.my_method = ...    -> vive en la clase   -> TODAS las instancias,
#                           incluso las ya creadas (buscan al llamar,
#                           no guardaron copia).
#   d.my_method  = ...   -> vive en d.__dict__ -> SOLO d. Tapa al de
#                           la clase. `del d.my_method` lo revierte.
#
# Cómo elegir: ¿el hook es una propiedad del TIPO (todo D debe
# loguear) o de ese OBJETO concreto (quiero instrumentar este para
# depurar)? Esa pregunta decide.


if __name__ == "__main__":
    print("--- (a) patch en la clase ---")
    DPatched().my_method()

    print("\n--- (b) patch en la instancia ---")
    solo_este = patch_instance(D())
    solo_este.my_method()
    print("otra instancia NO afectada:")
    D().my_method()                      # solo imprime "D"

    print("\n--- (c) subclase ---")
    DSub().my_method()

    print("\n--- (d) decorador de clase ---")
    r = Repo()
    print(r.get(1))
    print(r._internal())                 # sin hooks: empieza con _

    print("\n--- (e) proxy ---")
    DProxy().my_method()

    print("\n--- (f) context manager ---")
    with hooks():
        D().my_method()

    print("\n--- functools.wraps ---")
    print("con wraps   :", DPatched.my_method.__name__)
    def sin_wraps(f):
        def wrapper(*a, **k): return f(*a, **k)
        return wrapper
    print("sin wraps   :", sin_wraps(D.my_method).__name__)
