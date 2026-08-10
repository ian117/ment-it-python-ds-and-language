"""
EPAM — Práctica pregunta por pregunta.

=============================================================
P1 — Promedio de temperatura por ciudad
=============================================================
"From a list of tuples containing the info of a city and temperature,
 return the average temperature for each city."

Entrada:  [("mx", 30), ("ny", 10), ("mx", 20), ("ny", 14), ("bcn", 25)]
Salida:   {"mx": 25.0, "ny": 12.0, "bcn": 25.0}

Escribe tu solución abajo. Cuando termines, prepárate para responder
en voz alta (como en la entrevista):
  1. ¿Cuál es la complejidad en tiempo y en memoria?
  2. ¿Por qué elegiste esa estructura de datos y no otra?
  3. ¿Qué pasa si la lista viene vacía?
"""

readings = [("mx", 30), ("ny", 10), ("mx", 20), ("ny", 14), ("bcn", 25)]

# hacer un diccionario | hashmap para ir guardando las ciudades y numero de instancias de la ciudad
# si la ciudad ya existe, aumentar el valor y el # de instancias
# despues hacer una obtencion del avg
#   por cada ciudad, div valor/#instancias encontradas y guardar
#  Ya con la info, formatear el string f"City 1 : numero, City 2: numero"

from collections import defaultdict

def average_by_city(readings):
    formattedStr = ''
    sums, counts = defaultdict(float),defaultdict(int)
    for city, temp in readings:
        sums[city] += temp
        counts[city] += 1
    
    avgDicc = {city: sums[city] / counts[city] for city in sums}

    start = True
    for city,avg in avgDicc.items():
      if start:
        formattedStr = f"{city}: {avg}, "
        start = False
      else:
         formattedStr += f" {city}: {avg},"
          
    return formattedStr
        



if __name__ == "__main__":
    print(average_by_city(readings))
