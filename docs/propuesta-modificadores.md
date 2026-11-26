# Propuesta: sintaxis de modificadores de línea en `input.txt`

El enunciado indica que el archivo de entrada puede especificar líneas que **no permiten transbordos** en ciertos momentos, o líneas que **duplican su tiempo de viaje** por retrasos técnicos. El ejemplo de `input.txt` no incluye una sintaxis para esto, por lo que proponemos la siguiente.

## Formato

Una sección **opcional** al final del archivo, después de los datos de la misión, con un modificador por línea:

```text
# Datos de la Misión: Origen_Pierre | Origen_Amélie | Destino_Búnker_P | Destino_Búnker_A
1 12 7 8
# Modificadores (opcional): Tipo | Línea | Minuto_Inicio | Minuto_Fin
SIN_TRANSBORDO L4 10 30
TIEMPO_DOBLE L1 0 45
TIEMPO_DOBLE L9
```

## Tipos de modificador

**`SIN_TRANSBORDO <línea> [inicio fin]`**
Durante el intervalo, nadie puede **iniciar** un transbordo hacia esa línea ni desde ella, en ninguna estación. Los trenes de la línea siguen funcionando: se puede seguir viajando en ella sin cambiar de línea, y se puede abordar en la estación de origen (eso no es un transbordo). Un transbordo iniciado antes del intervalo se completa normalmente.

**`TIEMPO_DOBLE <línea> [inicio fin]`**
Todo túnel de esa línea en el que se entre durante el intervalo tarda el doble de su tiempo de viaje. Si dos intervalos se superponen, el tiempo sigue siendo el doble (no se acumula).

## Reglas generales

- Los tiempos están en **minutos desde el inicio de la operación**, la misma unidad que el resto del problema.
- El intervalo incluye el minuto de inicio y excluye el de fin: `10 30` abarca los minutos 10 a 29.
- Si se omiten los minutos, el modificador está activo durante **toda la operación**.
- La sección es opcional: un archivo con exactamente el formato del enunciado sigue siendo válido.

- Se escriben los dos minutos o ninguno, y la línea se escribe igual que en los túneles (`L4`, `L9`, …).

## Estado

El profesor pidió esta sintaxis por correo para poder usarla.
