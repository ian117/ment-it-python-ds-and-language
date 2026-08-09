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



def average_by_city(readings):
    citySearch = {} # { city:"london", count: #, valueRaw: # }
    formattedStr = ''
    for i, item in enumerate(readings):
        if citySearch.get(readings[i][0]) == None:
            citySearch[readings[i][0]] = { 'count': 1, 'valueRaw': readings[i][1] }
        else:
            citySearch[readings[i][0]]['count'] += 1
            citySearch[readings[i][0]]['valueRaw'] += readings[i][1]
    
    start = True
    for clave in citySearch:
        citySearch[clave]['avg'] = (citySearch[clave]['valueRaw'] / citySearch[clave]['count'])
        if start:
          formattedStr += f'{clave}: {citySearch[clave]["avg"]}'
          start = False
        else:
          formattedStr += f', {clave}: {citySearch[clave]["avg"]}'
          
    return formattedStr
        



if __name__ == "__main__":
    print(average_by_city(readings))
