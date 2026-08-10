"""
=============================================================
P5 — Diseño que soporte scraping Y API
=============================================================
Pregunta de DISEÑO, no de implementación.

    CNN -> release -> API -> extract articles

Dos formas de obtener artículos:
  - Scraping (lo implementamos nosotros)
  - API      (la consumimos)

El entrevistador te dio esta clase de partida:

    class NewsScrappingService:
        def __init__(self, url):
            self.url = url
        def scrapper(self):   # Extract articles cnn.com
            ...

"What would be your design to support both extraction ways?"

TU TAREA (escribe las firmas y los contratos; los cuerpos pueden
ser `...`, lo que se evalúa es la ESTRUCTURA)

  1. Critica la clase de partida: ¿qué está mal en su nombre y en
     que reciba `url` en el constructor?
  2. Define el modelo de dominio común (¿qué campos?).
  3. Define el contrato/interfaz. ¿Cuántos métodos debe tener y
     por qué el mínimo posible?
  4. Escribe los dos adaptadores.
  5. Escribe el servicio que los orquesta. Pregunta clave:
     ¿cómo recibe las fuentes? ¿por qué NO con un if?
  6. Nombra los 3 patrones de diseño que usaste.
  7. Recorre los 5 principios SOLID y di dónde aparece cada uno.

PRUEBA DE FUEGO (E8): mañana piden soportar un feed RSS.
¿Qué archivos tocas y cuáles NO? Si tu respuesta incluye modificar
el servicio, el diseño falló.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


# --- 1. Crítica a la clase de partida:


# --- 2. Modelo de dominio:


# --- 3. El contrato:


# --- 4. Los adaptadores:


# --- 5. El servicio:


# --- 6. Patrones usados:


# --- 7. SOLID:
