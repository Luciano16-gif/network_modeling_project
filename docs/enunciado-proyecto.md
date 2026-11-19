# El Escape de los Coleccionistas en el Metro de París

> Transcripción fiel de [`enunciado-proyecto.pdf`](enunciado-proyecto.pdf), el enunciado oficial del proyecto.
> Universidad Metropolitana — Departamento de Modelación de Sistemas en Redes — Trimestre 2627-1.
> Si hay alguna discrepancia, el PDF es la fuente de verdad.

## 1. Contexto

**París** es mundialmente famosa por su historia, su arte y su impresionante e intrincado sistema de transporte subterráneo. El **Metro de París** es una densa red de líneas interconectadas donde las estaciones actúan como nodos y los túneles como aristas.

**Pierre y Amélie** son dos ávidos coleccionistas de arte moderno y de criptoactivos físicos. Recientemente, han adquirido dos piezas exclusivas y sumamente valiosas en distintos puntos de la ciudad. Sin embargo, la organización rival "Le Sindicat" se ha enterado del intercambio y ha desplegado agentes en el metro para interceptarlos.

Para evitar levantar sospechas y minimizar el riesgo de que los capturen con ambas piezas juntas, Pierre y Amélie deben moverse por el metro **completamente separados** (nunca pueden coincidir en la misma estación al mismo tiempo ni cruzar el mismo túnel simultáneamente). Su objetivo es encontrarse en una **Estación Segura (búnker clandestino)** para resguardar las obras.

El conserje del búnker les ha puesto una condición estricta: para abrir las compuertas neumáticas de seguridad sin activar las alarmas del vecindario, **ambos deben presionar los botones de acceso en las dos entradas del búnker exactamente en el mismo segundo**. Si uno llega antes, deberá esperar en los pasillos de transbordo exteriores expuesto al peligro, acumulando "puntos de riesgo" por minuto de desfase.

## 2. Especificación Técnica de la Red y el Entorno

La red del metro se modelará como un **Grafo Dirigido y Ponderado G = (V, E)**.

- **Vértices (V):** Estaciones del metro. Cada estación tiene un identificador único (ID numérico) y un **Tiempo de Transbordo Interno** (en minutos) si se cambia de línea.
- **Aristas (E):** Los túneles que conectan estaciones consecutivas. Cada arista tiene un peso W(e) que representa el **tiempo de viaje del tren en minutos**.
- **Líneas de Metro:** Las aristas pertenecen a líneas específicas (Línea 1, Línea 4, etc.). Pasar de una arista de la Línea 1 a una arista de la Línea 4 en una misma estación penaliza el camino sumando el *Tiempo de Transbordo Interno* de esa estación al costo total.

### Puntos de Partida y Destinos (Variables de Entrada)

- **Origen de Pierre (O_P):** Estación donde inicia Pierre.
- **Origen de Amélie (O_A):** Estación donde inicia Amélie.
- **El Búnker (D):** Estación de destino común. Tiene dos compuertas de acceso independientes (D₁ y D₂). Pierre debe entrar por D₁ y Amélie por D₂.

### Restricciones Especiales

1. **Condición de No-Colisión Temporal:** Pierre y Amélie no pueden estar en la misma estación v ∈ V en el mismo instante de tiempo exacto (medido en minutos desde el inicio de la simulación).
2. **Condición de No-Colisión Espacial:** No pueden viajar en el mismo tren ni cruzarse en el mismo túnel al mismo tiempo en sentidos opuestos.
3. **Restricción de Líneas Clausuradas:** Debido a mantenimientos imprevistos del metro, el archivo de entrada puede especificar que **ciertas líneas completas no permiten transbordos** en horas específicas, o que un color de línea específico duplica su tiempo de viaje debido a retrasos técnicos.

## 3. Requerimientos del Programa

El programa debe leer un archivo de texto (`input.txt`) que describe el estado del metro y los puntos de partida de los personajes. Debe procesar la información de manera óptima y generar un reporte detallado.

**El algoritmo deberá calcular:**

1. **La Ruta de Costo Mínimo Sincronizada:** Determinar la trayectoria exacta que debe seguir Pierre y la que debe seguir Amélie para llegar al búnker.
2. **Minimización del Tiempo Total de la Operación:** Se define como el tiempo del personaje que realiza el viaje más largo (T_max = max(T_P, T_A)).
3. **Cálculo del Desfase de Salida:** Si la ruta óptima sin colisiones implica que Pierre tarda 25 minutos y Amélie tarda 18 minutos, el programa debe indicar explícitamente que **Amélie debe retrasar su salida exactamente 7 minutos** respecto a Pierre para garantizar la llegada simultánea al búnker a los 25 minutos de iniciada la operación.

## 4. Formato de los Archivos (Input / Output)

### Ejemplo de `input.txt`

```text
# Número de estaciones, número de túneles
15 22
# Estación | Tiempo de Transbordo
1 2
2 3
3 1
...
# Túneles: Estación_Origen | Estación_Destino | Tiempo_Viaje | Línea
1 2 4 L1
2 3 3 L1
3 4 5 L4
...
# Datos de la Misión: Origen_Pierre | Origen_Amélie | Destino_Búnker_P | Destino_Búnker_A
1 12 7 8
```

### Ejemplo de `output.txt`

```text
=== PLAN DE ESCAPE CONFIGURADO ===
Tiempo Total de la Operación: 28 minutos

[PROGRAMACIÓN DE SALIDAS]
* Pierre arranca en el minuto: 0
* Amélie arranca en el minuto: 6 (Debe esperar 6 minutos en su estación de origen)

[RUTA DE PIERRE (Tiempo total de viaje: 28 min)]
Minuto 0: Estación 1 (Origen)
Minuto 4: Estación 2 (Viaje L1)
Minuto 7: Estación 2 (Termina Transbordo a L4)
Minuto 15: Estación 5 (Viaje L4)
...
Minuto 28: Estación 7 (Destino Compuerta D1)

[RUTA DE AMÉLIE (Tiempo total de viaje: 22 min)]
Minuto 6: Estación 12 (Origen - Inicia Movimiento)
Minuto 11: Estación 14 (Viaje L9)
...
Minuto 28: Estación 8 (Destino Compuerta D2)

Resultado de Sincronización: ÉXITO. Llegada simultánea en el minuto 28.
```

## 5. Condiciones de la entrega

- El proyecto deberá ser programado en **Python**.
  - Todo el código debe ser realizado por el equipo. Deberá seleccionar **una de las cinco representaciones vistas en clase** para almacenar su grafo en memoria y deberá justificar la selección el día de la defensa.
  - **No pueden utilizar ninguna librería de terceros.**
- Deberán traer un computador portátil el día de la defensa del proyecto. Deberán asistir todos los miembros de su equipo.
- En la defensa se les preguntará sobre el propósito de los diferentes métodos que integran el programa y deberán poder justificar todo lo realizado.
- Deberán subir el programa fuente al aula virtual junto con el archivo de entrada y el archivo de salida, **tres archivos en total**, a más tardar el **domingo 29 de noviembre antes de medianoche**.
- El proyecto será defendido el **martes 1.º de diciembre** durante la hora de clase.
