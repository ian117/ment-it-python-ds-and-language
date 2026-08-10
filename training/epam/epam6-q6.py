"""
=============================================================
P6 — Estrategia de testing (y no gastar dinero)
=============================================================
Sobre el diseño de P5, te preguntaron:
  - ¿Qué estrategia de testing usarías?
  - ¿Qué librerías de Python?
  - "Este servicio llama a una API, una API REAL. ¿Necesitas hacer
     algo específico? ¿Hay que estar pendiente de algo?"

INSISTIERON en esto: cada llamada CUESTA DINERO, y debe haber una
manera —en la lógica y en los tests— de prevenir gastar de más.
Esa es la parte que de verdad evaluaban.

TU TAREA
  1. Describe la pirámide: qué niveles de test, qué prueba cada uno
     y cuántos de cada uno.
  2. Diferencia stub / mock / fake / spy con un ejemplo de cada uno
     aplicado a P5.
  3. Lista las librerías que usarías y para qué sirve cada una.
  4. Tres razones concretas de por qué los tests NO llaman a la API
     real. Ordénalas por importancia.
  5. ¿En qué CAPA hay que mockear? ¿Por qué mockear
     CnnApiSource.fetch() no prueba nada?
  6. Enumera 5+ mecanismos EN CÓDIGO DE PRODUCCIÓN para no quemar
     la cuota de la API.
  7. Escribe los tests (E10) con `responses`:
        a) happy path: parsea 2 artículos
        b) un 500 se reintenta 3 veces
        c) un 401 NO se reintenta
        d) dos llamadas con caché caliente = 1 sola petición HTTP
     Los dos últimos son tests DEL CONTROL DE GASTO y son gratis.

PREGUNTA 💬 (E11): tu jefe dice "los mocks no prueban nada real,
hagamos que los tests peguen a la API de verdad". Da 3 argumentos
en contra y una propuesta que le dé lo que quiere sin quemar
presupuesto.
"""

# --- 1. Pirámide:


# --- 2. Stub / mock / fake / spy:


# --- 3. Librerías:


# --- 4. Por qué no llamar a la API real:


# --- 5. Dónde mockear:


# --- 6. Protecciones en producción:


# --- 7. Los tests:


# --- 💬 Respuesta al jefe:
