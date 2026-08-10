"""
=============================================================
P2 — ¿Qué imprime d.my_method()?
=============================================================
El entrevistador te escribió ESTE código (tal cual, con errores) y
preguntó: "¿qué imprimirá al final?"

    import abc import abc, abstractmethod

    class A (ABC):
        abstractmethod
        def my_method():
            print("A")
    class B(A)
        def my_method():
            print("B")
    class C(A)
        def my_method():
            print("C")
    class D(B,C)
        ...

    d = D()
    d.my_method()   # ¿qué imprime?

TU TAREA (contesta en los comentarios de abajo, SIN correr nada):

  1. ¿Qué imprime? ¿Por qué ese y no otro?
  2. El código tiene 4 errores. Encuéntralos.
     (pista: uno es de import, uno de decorador, uno de firma de
      método, y uno se repite 3 veces)
  3. ¿Cuál es el __mro__ de D, en orden?
  4. Hubo énfasis extra en constructores: si A, B, C y D tuvieran
     __init__, ¿qué hay que hacer para que TODOS se ejecuten una vez?
     ¿Por qué NO sirve llamar A.__init__(self)?
"""

# --- 1. Qué imprime:


# --- 2. Los 4 errores:
# 1.    que es from en 2do import
# 2.    no se usa el "@"
# 3.    El abc esta en minus (en el import erroeno) y se tiene que importar en mayus
# 4.    Falta el self

# --- 3. El MRO de D:
    # Segun recuerdo, es de izquierda a derecha la jerarquia no? por lo que se imprimiria la "B" si preguntamos que se hereda por jerarquia

# --- 4. Constructores y super():


# =============================================================
# Cuando hayas contestado, escribe abajo la versión CORREGIDA
# y córrela para comprobar tu respuesta.
# =============================================================

# Method Resolution Object

from abc import ABC, abstractmethod

class A (ABC):
    @abstractmethod
    def my_method(self):
        print("A")
    
class B(A):
    def __init__(self):
        super().__init__()

    def my_method(self):
        print("B")

class C(A):
    def __init__(self):
        super().__init__()

    def my_method(self):
        print("C")

class D(B,C):
    ...

# MRO METHOD resulution order    D.my_method()   ->   B.my_method() ->  C.my_method()   ->  A.my_method()   


d = D()
d.my_method()   # ¿qué imprime?
