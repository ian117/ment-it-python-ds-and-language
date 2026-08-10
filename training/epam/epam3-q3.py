"""
=============================================================
P3 — Pre/post proceso sin modificar el método
=============================================================
Lo que te dieron:

    class D():
        def my_method(self):
            # can't modify this method
            print("D")

    d = D()
    d.my_method()   # before -> 'preproc' and after -> 'postproc'

Salida esperada:
    preproc
    D
    postproc

"How can you achieve this behaviour with Python?"

TU TAREA
  1. Resuélvelo SIN tocar el cuerpo de my_method.
  2. Nombra al menos 3 técnicas distintas para lograrlo y di
     cuándo usarías cada una.
  3. ¿Qué hace functools.wraps y qué se rompe si lo omites?
  4. ¿Tu solución afecta a d, o a TODAS las instancias de D?
     ¿Cómo harías la otra variante?
"""


class D:
    def my_method(self):
        # no puedes modificar este método
        print("D")


# --- 1. Tu solución:


# --- 2. Otras técnicas (comentario):


# --- 3. functools.wraps:


# --- 4. Instancia vs clase:


if __name__ == "__main__":
    d = D()
    d.my_method()
