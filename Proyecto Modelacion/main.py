def cargar_datos_metro(ruta_archivo):
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        lineas = archivo.readlines()
    linea2 = []
    for k in lineas:
        linea2 = k.strip()
        if linea2 and not linea2.startswith('#'):
            linea2.append(linea2.split())

    num_estaciones = int(linea2[0][0])
    num_tuneles = int(linea2[0][1])
    indice_actual = 1
    estaciones = {}
    for i in range(num_estaciones):
        id_estacion = int(linea2[indice_actual][0])
        tiempo_trans = int(linea2[indice_actual][1])
        estaciones[id_estacion] = tiempo_trans
        indice_actual += 1

    tuneles = []
    for j in range(num_tuneles):
        origen = int(linea2[indice_actual][0])
        destino = int(linea2[indice_actual][1])
        tiempo_viaje = int(linea2[indice_actual][2])
        linea_metro = linea2[indice_actual][3]
        
        tuneles.append({
            'origen': origen,
            'destino': destino,
            'tiempo': tiempo_viaje,
            'linea': linea_metro
        })
        indice_actual += 1

    datos_mision = linea2[indice_actual]
    mision = {
        'origen_pierre': int(datos_mision[0]),
        'origen_amelie': int(datos_mision[1]),
        'destino_bunker_p': int(datos_mision[2]),
        'destino_bunker_a': int(datos_mision[3])
    }
    return estaciones, tuneles, mision


def crearMatrizAdy(estaciones):
    matriz = []
    for i in range(estaciones):
        submatriz = []
        for j in range(estaciones):
            if(i == j):
                submatriz.append(0)
            else:
                submatriz.append(999)
        matriz.append(submatriz)

def main():
    print("hoal")