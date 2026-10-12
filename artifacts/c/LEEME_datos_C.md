# LEEME — Datos y notebook de reglas de asociación (Parte V)

Este documento explica el contenido real de [`artefactos_C/`](artefactos_C/) y de [`Parte5_Reglas_Asociacion_PersonaC.ipynb`](Parte5_Reglas_Asociacion_PersonaC.ipynb), su relación con el proyecto y cómo utilizar sus resultados en el reporte web.

La explicación se basa en el código, las salidas guardadas del notebook y los ocho archivos entregados. No se volvió a ejecutar el procesamiento con Spark: los Parquet de entrada no están en esta carpeta. Las cifras corresponden a la ejecución guardada, no a una nueva descarga o actualización de los datos.

## 1. Qué aporta esta parte al proyecto

Según [`proyecto.md`](proyecto.md), el equipo debe aplicar técnicas de minería sobre datos públicos peruanos y comunicar los hallazgos mediante una página web interactiva. Según [`reparticion.md`](reparticion.md), el trabajo se distribuye así:

| Integrante | Responsabilidad principal | Relación con esta entrega |
|---|---|---|
| A | Ingesta y limpieza, similitud y búsqueda aproximada de vecinos | Proporciona los datos preparados que necesita C. |
| B | EDA, minería de flujos y construcción e integración de la web | Consume los artefactos de C para mostrar resultados y filtros. |
| C | Agregaciones y particionamiento, reglas de asociación, README y presentación | Produce el notebook y los resultados descritos aquí. |

El notebook cubre las tareas **4, 16, 17, 18 y 19**: dos agregaciones en Spark, particionamiento, construcción de transacciones, Apriori, FP-Growth y generación/selección de reglas. También exporta resultados para la integración de B. Aunque su nombre dice «Parte5», contiene trabajo de la **Parte I** y de la **Parte V**.

La discusión de la Parte VI corresponde a los tres integrantes. Este LEEME documenta el bloque C; el README general con instrucciones de la web y la presentación completa son entregables adicionales de C que no aparecen en esta carpeta.

## 2. Qué datos analiza

El encabezado del notebook identifica la fuente como **SEACE/OCDS, enero de 2024 a agosto de 2026, OECE vía Open Contracting**, y declara licencia CC BY 4.0. Estos datos de procedencia se reproducen del notebook; la descarga y su verificación no forman parte de este archivo.

Aunque la repartición plantea SEACE/OCDS + SUNAT Padrón RUC, este notebook no descarga SUNAT ni realiza un cruce con ese padrón. Parte de tablas Parquet ya preparadas.

| Dato de la ejecución guardada | Valor |
|---|---:|
| Filas de `procesos` leídas | 209 740 |
| Filas de `items` leídas | 243 699 |
| Transacciones utilizadas para asociación | 196 158 |
| Filas de procesos excluidas al formar transacciones | 13 582 |
| Ítems distintos en las transacciones | 151 |
| Tamaño de cada canasta | Entre 8 y 18 ítems; promedio 8,84 |
| Transacciones de la muestra de Apriori | 30 188 |

La unidad de análisis elegida es un proceso identificado por `release_id`. El notebook presupone que la preparación previa dejó la granularidad correcta; no verifica allí la unicidad de esa clave en `procesos`.

Las preguntas del bloque son: **¿qué combinaciones de características se asocian con estados DESIERTO o NULO? ¿Cómo se distribuyen esos patrones entre los períodos que el código etiqueta como anteriores y posteriores al 22 de abril de 2025?** La segunda pregunta está planteada, pero no queda resuelta con una comparación temporal completa en las salidas entregadas.

## 3. Cómo leer el notebook

El archivo tiene 21 celdas. Para comprenderlo, puede abrirse en Jupyter, VS Code o Google Colab y leer sus salidas existentes sin ejecutar las celdas.

| Bloque | Qué hace | Dónde se ejecuta |
|---|---|---|
| 0. Preparación | Instala PySpark 3.5.3 en Colab, monta Drive y lee cinco tablas Parquet. | Spark en modo `local[*]`. |
| 1. Agregaciones y particionamiento | Compara RDD con DataFrame y prueba distintas reparticiones. | Spark. |
| 2. Transacciones | Transforma cada proceso admitido en una canasta de etiquetas. | Spark. |
| 3. Apriori | Busca conjuntos frecuentes mediante generación de candidatos y poda. | Python y NumPy, sobre una muestra en memoria. |
| 4. FP-Growth | Busca conjuntos frecuentes en la misma muestra y en todas las transacciones admitidas. | Spark MLlib. |
| 5. Reglas | Calcula soporte, confianza y lift; marca reglas y selecciona candidatas. | Python y pandas, a partir de los conjuntos frecuentes. |
| 6. Exportación | Escribe CSV y JSON para reutilizar los resultados. | Sistema de archivos indicado por `OUT`. |

`local[*]` utiliza los núcleos disponibles en una sola máquina. Se emplean las operaciones y el motor de Spark, pero esta ejecución no acredita rendimiento en un clúster de varias máquinas.

### 3.1. Agregaciones y particionamiento: tarea 4

Se implementan dos cálculos tanto con RDD (`map`, `reduceByKey`) como con DataFrame (`groupBy`, `agg`):

1. **Por departamento de la entidad:** cantidad de procesos, suma y promedio de `valor_pen_valido`.
2. **Por procedimiento y categoría:** cantidad de procesos, cantidad con estado DESIERTO y tasa de DESIERTO. Excluye `CONVOCADO` y `sin_dato` y conserva grupos con al menos 200 registros.

Cada agregación se mide tres veces; se imprimen el mínimo y la mediana.

| Agregación | DataFrame: mínimo / mediana | RDD: mínimo / mediana |
|---|---:|---:|
| Procesos y montos por departamento | 1,24 / 1,30 s | 3,44 / 3,97 s |
| Tasa de DESIERTO por procedimiento y categoría | 1,61 / 2,10 s | 3,62 / 4,34 s |

En esa ejecución, DataFrame fue más rápido. El primer cálculo muestra los mismos tres departamentos líderes en cantidad de procesos en ambos enfoques: Lima, 62 796; Cusco, 17 847; Áncash, 11 935. Esa salida no constituye una comprobación completa de igualdad de todas las columnas y grupos.

La sección de particionamiento diferencia tres conceptos:

- **Particiones de almacenamiento por `anio_pub`:** permiten omitir archivos de otros años al filtrar por 2025; el plan muestra `PartitionFilters`.
- **Particiones de lectura:** la ejecución muestra 3, que no deben confundirse con el número de años o con la configuración de shuffle.
- **Redistribución durante el cálculo:** `groupBy` introduce un intercambio de datos (`Exchange hashpartitioning`). La configuración observada de `spark.sql.shuffle.partitions` es 200.

Se prueban `repartition(n)` y `repartition(n, "entidad_departamento")`. El mejor tiempo observado fue aproximadamente **0,303 s** con cuatro particiones por departamento, frente a **4,128 s** con `repartition(200)`. Son mediciones locales que incluyen el trabajo de repartición y agregación, sobre una base cacheada; no prueban que esa configuración sea óptima para cualquier volumen o equipo.

También se evidencia desequilibrio al repartir por departamento: con ocho particiones, sus tamaños van de 3 976 a 74 055 filas. Agrupar por una clave puede facilitar la agregación y, al mismo tiempo, concentrar trabajo en algunas particiones.

### 3.2. Construcción de canastas: tarea 16

Una canasta es un conjunto de características, no una compra de supermercado. Por ejemplo:

```text
{cat=services, proc=Adjudicación Abreviada, tipo=otro,
 dep=LIMA, monto=sin_dato, postores=2-4,
 ley=anterior, estado=CONTRATADO, seg=76}
```

El código excluye estados `CONVOCADO` y `sin_dato`, une los segmentos de `items` por `release_id` y elimina etiquetas duplicadas dentro de cada canasta. Los prefijos permiten distinguir variables.

| Prefijo | Origen y significado |
|---|---|
| `cat=` | `categoria`: por ejemplo `goods` (bienes), `services` (servicios) y `works` (obras). |
| `proc=` | `procedimiento`: denominación del procedimiento de contratación. |
| `tipo=` | `entidad_tipo`: clasificación de la entidad recibida de la preparación previa. El notebook la describe como heurística. |
| `dep=` | `entidad_departamento`: sede de la entidad; no representa necesariamente el lugar de ejecución. |
| `seg=` | `items.unspsc_segmento`: códigos de segmento UNSPSC. Un proceso puede aportar varios o ninguno; no se adjunta un catálogo de nombres. |
| `monto=` | Tramo de `valor_pen_valido`, o una etiqueta especial cuando falta el monto. |
| `postores=` | Tramos de `n_postores`: `0`, `1`, `2-4`, `5-9`, `10+`. |
| `ley=` | Etiqueta temporal según `fecha_pub`: `anterior` antes de `2025-04-22`; `nueva_32069` desde esa fecha. No verifica individualmente la norma aplicable al proceso. |
| `estado=` | `estado_proceso`; conserva ocho estados principales y agrupa los restantes admitidos en `OTRO`. |

Los estados conservados son `CONTRATADO`, `DESIERTO`, `NULO`, `CONSENTIDO`, `ADJUDICADO`, `MIXTO`, `CANCELADO` y `RETROTRAIDO_POR_RESOLUCION`. `estado=NULO` es una etiqueta del estado del proceso, **no un valor ausente de Python o SQL**. Excluir convocados tampoco significa que todos los estados restantes sean finales.

Los cuartiles se calculan aproximadamente sobre todos los procesos con monto válido, **antes de excluir estados para las canastas**, con error relativo configurado de 0,001:

| Etiqueta | Condición en la ejecución guardada |
|---|---|
| `monto=Q1_bajo` | Monto válido ≤ S/ 90 360,00. |
| `monto=Q2` | S/ 90 360,00 < monto ≤ S/ 195 000,00. |
| `monto=Q3` | S/ 195 000,00 < monto ≤ S/ 506 325,85. |
| `monto=Q4_alto` | Monto > S/ 506 325,85. |
| `monto=protegido` | Monto válido nulo e `info_protegida` verdadera. |
| `monto=sin_dato` | Monto válido nulo sin cumplir la condición anterior. |

Por ello, los cuatro tramos no tienen necesariamente el 25 % de las transacciones finales. `protegido` tampoco significa monto cero.

### 3.3. Apriori y FP-Growth: tareas 17 y 18

**Apriori** comienza por ítems frecuentes, forma candidatos de mayor tamaño y descarta aquellos con subconjuntos no frecuentes. Usa una matriz booleana de NumPy para contar ocurrencias. En este código tiene un límite de **cinco ítems por conjunto** (`max_k=5`).

La muestra se obtiene sin reemplazo, con semilla 42 y una fracción calculada para esperar 30 000 registros. El muestreo es probabilístico: el tamaño obtenido fue **30 188**, no exactamente 30 000.

**FP-Growth** usa la implementación de Spark MLlib, sin imponer ese límite de cinco ítems. Se aplica primero a las mismas transacciones muestreadas y luego a las **196 158 transacciones filtradas**. «Completo» en los archivos significa este universo, no todos los registros originales ni todo SEACE.

| Ejecución | Transacciones | Soporte mínimo | Conjuntos frecuentes | Tiempo |
|---|---:|---:|---:|---:|
| Apriori, muestra | 30 188 | 2 % | 1 969 | 1,684 s |
| FP-Growth, misma muestra | 30 188 | 2 % | 2 005 | 7,734 s |
| FP-Growth, completo filtrado | 196 158 | 1 % | 5 002 | 15,643 s |

El notebook imprime **`¿Mismos itemsets y mismos conteos? False`**. La comparación tiene distintos límites de tamaño; no es una validación satisfactoria de equivalencia. Para comprobarla, habría que comparar Apriori con los resultados de FP-Growth de tamaño ≤ 5, o quitar el límite de Apriori. Los conjuntos de ambas ejecuciones de muestra no se exportaron, por lo que no se puede verificar aquí que esa sea la única causa de la diferencia.

El menor tiempo de Apriori en esta prueba no demuestra que sea mejor en cualquier escenario: corre en memoria local, limita el tamaño de los conjuntos y evita parte del costo de Spark. Los tiempos de FP-Growth incluyen ajuste del modelo y recolección de conjuntos al controlador; la preparación de la muestra queda fuera de esas mediciones.

### 3.4. Generación de reglas: tarea 19

Un **ítem** es una etiqueta. Un **itemset** es un conjunto de etiquetas que aparecen juntas. Una **regla** divide un itemset en dos conjuntos no vacíos y sin elementos compartidos: antecedente **A** y consecuente **C**, escritos `A → C`.

| Métrica | Cálculo | Interpretación |
|---|---|---|
| Soporte | `n(A ∪ C) / N` | Proporción de todas las transacciones que contienen ambos lados. |
| Confianza | `soporte(A ∪ C) / soporte(A)` | Proporción de transacciones con A que también contienen C. |
| Lift | `confianza / soporte(C)` | Cuántas veces la frecuencia condicional de C supera su frecuencia general. |

Aquí `N = 196158`. Soporte y confianza se almacenan como proporciones: `0.30` significa 30 %. Lift es una razón: `3` significa tres veces la frecuencia de referencia. Un lift de 1 corresponde a independencia según esas frecuencias.

El código genera reglas en Python a partir de los itemsets completos con soporte mínimo **0,01**, y conserva confianza **≥ 0,30** y lift **≥ 1,0**. El `minConfidence=0.0` usado al crear el modelo Spark no es el umbral final de las reglas exportadas: estas se generan después con una función propia.

Se aplican dos marcas:

- `mismo_tipo`: verdadera si algún prefijo aparece a ambos lados. Esas reglas se eliminan antes de exportar. También puede afectar a segmentos `seg=` distintos, aunque varios segmentos por canasta sí sean posibles.
- `trivial_ley_proc`: verdadera si hay `ley=` en un lado y `proc=` en el otro. Es un criterio estructural de marcado; no prueba por sí solo que la relación sea determinista. Estas reglas **sí permanecen** en la exportación general; se excluyen del conjunto `RN` utilizado para seleccionar candidatas.

Se exportan **33 804 reglas**, de las cuales **9 110** tienen `trivial_ley_proc=true`. Al ocultarlas quedan **24 694**. Las reglas pueden tener varios ítems en ambos lados y no se restringen a predecir estados: algunas incluso incluyen el estado en el antecedente.

## 4. Contenido de `artefactos_C/`

Los CSV usan cabecera, coma como separador y punto decimal. Algunos campos contienen comas y están entre comillas: deben leerse con un lector CSV, no separando cada línea manualmente por comas. Los textos incluyen caracteres en español.

| Archivo | Registros, sin cabecera | Qué contiene y para qué sirve |
|---|---:|---|
| [`tarea4_particiones.csv`](artefactos_C/tarea4_particiones.csv) | 10 | Tiempos de agregación con diferentes reparticiones; gráfico de tiempo por estrategia y cantidad de particiones. |
| [`comparacion_apriori_fpgrowth.csv`](artefactos_C/comparacion_apriori_fpgrowth.csv) | 3 | Resumen de Apriori y FP-Growth; tabla comparativa con sus condiciones de ejecución. |
| [`curva_fpgrowth.csv`](artefactos_C/curva_fpgrowth.csv) | 4 | Número de itemsets y tiempo al variar soporte mínimo; curva de sensibilidad. |
| [`items_frecuencia.csv`](artefactos_C/items_frecuencia.csv) | 151 | Frecuencia de cada etiqueta individual; permite mostrar distribuciones y referencias generales. |
| [`itemsets_frecuentes.csv`](artefactos_C/itemsets_frecuentes.csv) | 5 002 | Conjuntos frecuentes del universo completo filtrado, con soporte mínimo del 1 %. |
| [`reglas_asociacion.csv`](artefactos_C/reglas_asociacion.csv) | 33 804 | Reglas generales y métricas; útil para análisis tabular. |
| [`reglas_asociacion.json`](artefactos_C/reglas_asociacion.json) | 33 804 objetos | Las mismas reglas y campos, en JSON; útil para la web. |
| [`reglas_seleccionadas.csv`](artefactos_C/reglas_seleccionadas.csv) | 12 | Candidatas destacadas, con una columna adicional de soporte del consecuente. |

### Diccionario de campos

**`tarea4_particiones.csv`**

| Campo | Tipo y significado |
|---|---|
| `estrategia` | Texto: `repartition(n)` o `repartition(n, dep)`. |
| `n_part` | Entero: cantidad solicitada al reparticionar. |
| `t_min_s` | Número: menor tiempo, en segundos, de tres repeticiones. |

No contiene los tiempos comparativos de RDD frente a DataFrame: esos están en las salidas del notebook y se transcriben en la sección 3.1 de este LEEME.

**`comparacion_apriori_fpgrowth.csv` y `curva_fpgrowth.csv`**

| Campo | Tipo y significado |
|---|---|
| `algoritmo` | Texto que identifica algoritmo y universo; solo aparece en la comparación. |
| `n_trans` | Entero: transacciones utilizadas; solo aparece en la comparación. |
| `min_sup` | Número: umbral de soporte como proporción. |
| `n_itemsets` | Entero: cantidad de conjuntos frecuentes encontrados. |
| `t_s` | Número: tiempo de esa ejecución, en segundos. |

La curva se calcula sobre las 196 158 transacciones:

| Soporte mínimo | Itemsets | Tiempo |
|---:|---:|---:|
| 5 % | 472 | 5,823 s |
| 2 % | 1 973 | 14,470 s |
| 1 % | 5 002 | 17,057 s |
| 0,5 % | 11 351 | 18,322 s |

El ensayo del 1 % se ejecuta de nuevo al construir la curva: por eso su tiempo difiere del de la comparación principal. **La curva solo guarda conteos y tiempos**; no entrega los 11 351 itemsets ni reglas adicionales del ensayo con soporte de 0,5 %.

**`items_frecuencia.csv` e `itemsets_frecuentes.csv`**

| Archivo / campo | Tipo y significado |
|---|---|
| Frecuencias: `item` | Texto: una etiqueta, por ejemplo `estado=DESIERTO`. |
| Frecuencias: `count` | Entero: transacciones que contienen esa etiqueta. |
| Itemsets: `itemset` | Texto: etiquetas unidas por el separador literal ` & `. |
| Itemsets: `freq` | Entero: transacciones que contienen todas las etiquetas del conjunto. |
| Ambos: `soporte` | Número: `count / 196158` o `freq / 196158`. |

El archivo de frecuencias incluye los 151 ítems, incluso los de soporte inferior al 1 %. El de itemsets contiene únicamente conjuntos frecuentes: 84 de tamaño 1, 637 de tamaño 2, 1 469 de tamaño 3, 1 630 de tamaño 4, 877 de tamaño 5, 239 de tamaño 6, 54 de tamaño 7, 11 de tamaño 8 y 1 de tamaño 9.

**Archivos de reglas**

| Campo | Tipo y significado |
|---|---|
| `antecedente` | Texto con las condiciones de A, unidas por ` & `. |
| `consecuente` | Texto con las condiciones de C, unidas por ` & `. |
| `soporte` | Número: frecuencia relativa conjunta de ambos lados. |
| `confianza` | Número: frecuencia de C dentro de las transacciones que contienen A. |
| `lift` | Número: confianza dividida por soporte del consecuente. |
| `k_ant` | Entero: cantidad de ítems del antecedente. |
| `k_cons` | Entero: cantidad de ítems del consecuente. |
| `trivial_ley_proc` | Booleano: marca estructural de cruce entre ley y procedimiento. |
| `mismo_tipo` | Booleano: prefijos compartidos entre ambos lados; todas las filas exportadas tienen valor falso. |
| `sup_consecuente` | Solo en seleccionadas: soporte de C cuando C es un único ítem. Queda vacío para consecuentes de varios ítems por cómo se construye la consulta. |

Los vacíos de `sup_consecuente` **no significan soporte cero** ni invalidan el lift: la función que genera reglas sí usa soportes de conjuntos. Para completar esa columna, puede buscarse el conjunto del consecuente en `itemsets_frecuentes.csv`.

En los archivos generales se redondea soporte a cinco decimales, confianza a cuatro y lift a tres. En `reglas_seleccionadas.csv` se conserva mayor precisión, por lo que pueden verse pequeñas diferencias. Los booleanos se escriben como `True`/`False` en CSV y `true`/`false` en JSON.

## 5. Cómo interpretar las reglas seleccionadas

Las 12 candidatas se obtienen reuniendo cuatro reglas con consecuente DESIERTO, dos con NULO, cuatro de soporte ≥ 2 % cuyo consecuente no empieza por `estado=`, y dos con alguna etiqueta `ley=` en el antecedente; cada grupo se ordena por lift. Luego se eliminan duplicados. Es una selección automática, no doce hallazgos independientes.

Las referencias generales son **DESIERTO: 12,88 %**, **NULO: 6,05 %**, **monto protegido: 3,89 %** y **cero postores registrados: 4,51 %**. En la siguiente tabla, soporte y confianza se muestran en porcentaje para facilitar la lectura.

| # | Regla | Soporte | Confianza | Lift | Lectura en el contexto de los datos |
|---:|---|---:|---:|---:|---|
| 1 | `monto=protegido & postores=0 → estado=DESIERTO` | 1,086 % | 38,66 % | 3,001 | Entre procesos con monto protegido y cero postores registrados, 38,66 % figuran como DESIERTO, unas tres veces la frecuencia general. |
| 2 | `ley=anterior & monto=protegido & postores=0 → estado=DESIERTO` | 1,022 % | 37,97 % | 2,947 | Restringir el patrón anterior al período etiquetado como anterior mantiene una confianza parecida. No establece un efecto del cambio normativo. |
| 3 | `postores=0 → estado=DESIERTO` | 1,599 % | 35,45 % | 2,752 | Cero postores registrados se asocia con mayor presencia de DESIERTO respecto del 12,88 % general. |
| 4 | `ley=anterior & postores=0 → estado=DESIERTO` | 1,292 % | 32,01 % | 2,485 | Dentro de ese período y con cero postores, aproximadamente uno de cada tres procesos figura como DESIERTO. |
| 5 | `ley=anterior & postores=0 & tipo=municipalidad → estado=NULO` | 1,196 % | 62,29 % | 10,291 | En ese grupo municipal, NULO es mucho más frecuente que el 6,05 % del universo completo. Conviene revisar la composición y calidad del grupo. |
| 6 | `postores=0 & tipo=municipalidad → estado=NULO` | 1,260 % | 59,51 % | 9,831 | La asociación entre municipalidad, cero postores y NULO también aparece sin restringir el período. Se solapa ampliamente con la regla 5. |
| 7 | `monto=protegido → ley=anterior & postores=0` | 2,692 % | 69,20 % | 17,147 | Entre los procesos con monto protegido, 69,20 % reúnen simultáneamente período anterior y cero postores. El consecuente exige ambas condiciones. |
| 8 | `ley=anterior & postores=0 → monto=protegido` | 2,692 % | 66,71 % | 17,147 | En sentido inverso, dos de cada tres procesos de ese grupo tienen monto protegido; puede reflejar cómo se registra o publica la información. |
| 9 | `ley=anterior & monto=protegido → postores=0` | 2,692 % | 72,43 % | 16,062 | Entre los montos protegidos del período anterior, 72,43 % registran cero postores. |
| 10 | `postores=0 → ley=anterior & monto=protegido` | 2,692 % | 59,70 % | 16,062 | Entre los procesos con cero postores, 59,70 % pertenecen al período anterior y tienen monto protegido. Comparte el mismo conjunto de tres condiciones de las reglas 7–9. |
| 11 | `cat=services & ley=anterior & proc=Regímen Especial & tipo=otro → dep=LIMA & estado=CONTRATADO & monto=Q1_bajo & postores=1 & seg=80` | 1,004 % | 87,91 % | 53,836 | Ese perfil de servicios coincide con una combinación muy específica de cinco características. El lift compara contra la frecuencia conjunta de las cinco, no contra Lima o CONTRATADO por separado. |
| 12 | `cat=services & estado=CONTRATADO & ley=anterior & proc=Regímen Especial & tipo=otro → dep=LIMA & monto=Q1_bajo & postores=1 & seg=80` | 1,004 % | 96,62 % | 53,251 | Al incluir CONTRATADO en el antecedente, casi todo el grupo reúne las cuatro características restantes. Ya no es una regla para anticipar el estado de un proceso. |

Las etiquetas mantienen la escritura de los archivos, incluida `Regímen Especial`.

Como ejemplo de los denominadores, la regla 1 aparece conjuntamente en **2 131 de las 196 158 transacciones**. Su confianza del 38,66 % se calcula únicamente entre las que cumplen el antecedente; no significa que el 38,66 % de todo el dataset sea DESIERTO con monto protegido.

Estos son patrones de coexistencia en registros observados. No prueban causalidad, irregularidades ni capacidad predictiva sobre procesos futuros. En particular, `postores=0` debe leerse como el valor registrado, y la combinación con información protegida merece revisar la semántica del dato original antes de atribuirla a ausencia real de competencia.

## 6. Cómo utilizar los archivos en la web

La entrega permite seguir la arquitectura de `proyecto.md`: **calcular una vez y explorar los resultados muchas veces**. La página puede cargar reglas, filtrarlas y mostrar su interpretación sin ejecutar Spark en cada interacción.

Usos recomendados de los archivos existentes:

- Tabla filtrable de reglas desde `reglas_asociacion.json`, con controles de soporte, confianza, lift y consecuente; opción para ocultar `trivial_ley_proc` y limitar `k_cons` a 1.
- Reglas destacadas e interpretación a partir de `reglas_seleccionadas.csv` y de la sección 5.
- Distribuciones de etiquetas desde `items_frecuencia.csv` y exploración de combinaciones desde `itemsets_frecuentes.csv`.
- Comparación de algoritmos y curva de sensibilidad desde sus CSV, mostrando siempre tamaño de muestra, umbral y límite de Apriori.
- Gráfico de particiones y tiempos desde `tarea4_particiones.csv`.

Los filtros operan sobre un catálogo previamente recortado: **soporte ≥ 0,01; confianza ≥ 0,30; lift ≥ 1,0**, además de la exclusión por `mismo_tipo`. Bajar los controles por debajo de esos umbrales no recupera reglas que no se exportaron. La curva de soporte de 0,5 % no amplía ese catálogo. Los filtros usan métricas redondeadas en los archivos generales.

### Diferencia con el formato propuesto en `formato_C.md`

[`formato_C.md`](formato_C.md) pide JSON con estructura `{"meta": {...}, "datos": [...]}` y antecedentes/consecuentes como listas. **El JSON entregado actualmente es una lista en la raíz y usa cadenas unidas por ` & `**. Por ejemplo, su primer objeto es:

```json
{
  "antecedente": "proc=Convenio",
  "consecuente": "dep=LIMA",
  "soporte": 0.01945,
  "confianza": 0.9235,
  "lift": 3.08,
  "k_ant": 1,
  "k_cons": 1,
  "trivial_ley_proc": false,
  "mismo_tipo": false
}
```

Si la web ya espera `meta` y `datos`, necesita adaptar la carga o convertir el archivo. Un adaptador de lectura, sin modificar los originales, puede ser:

```javascript
const respuesta = await fetch("./artefactos_C/reglas_asociacion.json");
if (!respuesta.ok) throw new Error("No se pudieron cargar las reglas");
const filas = await respuesta.json();
const paquete = {
  meta: {
    descripcion: "Reglas sobre procesos SEACE/OCDS filtrados",
    algoritmo: "FP-Growth y generación de reglas en Python",
    n_transacciones: 196158,
    min_support: 0.01,
    min_confidence: 0.30,
    min_lift: 1.0
  },
  datos: filas.map(fila => ({
    ...fila,
    antecedente: fila.antecedente.split(" & "),
    consecuente: fila.consecuente.split(" & ")
  }))
};
const visibles = paquete.datos.filter(regla =>
  !regla.trivial_ley_proc &&
  regla.soporte >= 0.02 &&
  regla.confianza >= 0.50 &&
  regla.lift >= 1.20
);
```

La ruta se ajusta a la estructura de la web y se sirve por HTTP. El JSON ocupa aproximadamente 7,9 MB; conviene cargarlo una vez y paginar la tabla.

Tampoco existen aquí las subcarpetas `asociacion/` y `spark/`, ni los archivos propuestos `transacciones_resumen.json`, `itemsets_frecuentes.json`, `comparacion_algoritmos.json`, `texto_asociacion.md` y `comparacion_rdd_dataframe.json`. Parte de esa información está disponible en CSV, en el notebook y en este documento, pero no en el esquema solicitado. Esta documentación no convierte ni renombra los artefactos.

## 7. Cómo reproducir el cálculo

Para volver a calcular resultados se necesitan los datos preparados por A y un entorno compatible con PySpark 3.5.3, Java, NumPy y pandas. La primera celda ejecutable está diseñada específicamente para Google Colab.

1. Conseguir las cinco tablas Parquet y conservar esta estructura bajo una ruta común:

   ```text
   parquet/
   ├── procesos/
   ├── items/
   ├── adjudicaciones/
   ├── contratos/
   └── entidades/
   ```

2. En Colab, ejecutar la instalación de PySpark y montar Drive con acceso a las tablas. Para ejecutarlo localmente, sustituir la celda de instalación/montaje por la preparación del entorno local.
3. Cambiar `RUTA` al directorio que contiene las cinco tablas. Cambiar `OUT` al directorio de resultados; la exportación vuelve a escribir los archivos de esos nombres.
4. Ejecutar las celdas en orden. Se configura `spark.driver.memory` en `8g` y se utiliza `local[*]`; la disponibilidad real de memoria depende del entorno.
5. Revisar los conteos, cuartiles y salidas de validación antes de usar los nuevos artefactos. Los tiempos dependen del equipo, la caché y la ejecución.

El notebook lee `adjudicaciones`, `contratos` y `entidades`, aunque sus cálculos posteriores utilizan directamente `procesos` e `items`. Como está escrito, las cinco rutas deben existir.

Campos requeridos directamente por el código:

| Tabla | Columnas |
|---|---|
| `procesos` | `release_id`, `entidad_departamento`, `categoria`, `procedimiento`, `estado_proceso`, `valor_pen_valido`, `anio_pub`, `periodo`, `entidad_tipo`, `info_protegida`, `n_postores`, `fecha_pub`. |
| `items` | `release_id`, `unspsc_segmento`. |

Para explorar únicamente los resultados existentes basta con leer CSV/JSON; no se necesitan Spark ni los Parquet. Por ejemplo, desde esta carpeta:

```python
import pandas as pd

reglas = pd.read_json("artefactos_C/reglas_asociacion.json")
desierto = reglas[
    (reglas["consecuente"] == "estado=DESIERTO")
    & (~reglas["trivial_ley_proc"])
].sort_values("lift", ascending=False)
print(desierto.head(8).to_string(index=False))
```

## 8. Aspectos que deben tenerse presentes al presentar la entrega

- **Equivalencia de algoritmos pendiente:** la comprobación Apriori/FP-Growth guardada da `False`; los límites de tamaño deben igualarse para validarla.
- **Comparación temporal pendiente:** el texto de una salida dice «ley=nueva_32069», pero el filtro usa `str.contains("ley=")`, que incluye ambos períodos. Las dos candidatas finales contienen `ley=anterior`. Esa tabla no responde por sí sola qué cambió después de la fecha de corte.
- **Interpretación originalmente pendiente:** una celda de Markdown del notebook pide pegar resultados en un chat para redactar la interpretación. La sección 5 de este documento proporciona una lectura de las 12 candidatas que debe incorporarse al reporte y revisarse con el equipo.
- **Nulos en postores y fecha:** si llegaran nulos en `n_postores`, el encadenamiento actual de condiciones los enviaría a `postores=10+`. Una fecha nula caería en `ley=anterior`. Los Parquet no están disponibles aquí para comprobar si esos casos existen; hay que validar esos supuestos al reproducir.
- **Promedio RDD y montos cero:** el RDD usa la veracidad del monto para contar valores válidos, por lo que excluye ceros del denominador; DataFrame incluye ceros no nulos. Si `valor_pen_valido` admite ceros, sus promedios pueden diferir.
- **Entorno no completamente fijado:** se fija PySpark 3.5.3, pero no todas las dependencias. La salida de instalación guardada informa un conflicto con `dataproc-spark-connect`, aunque las celdas posteriores tienen resultados. Conviene resolver esa compatibilidad al preparar el entorno de reproducción.
- **Integración por completar:** no hay código de página web ni instrucciones reales para levantarla en esta entrega. Este bloque puede alimentar uno de los módulos interactivos; el proyecto exige al menos tres en el reporte global y la discusión conjunta de todas las técnicas.

Los artefactos permiten explorar los resultados calculados del bloque C. Para defenderlos en la exposición, deben explicarse sus denominadores, los filtros de selección y los límites de las comparaciones, además de mostrar las tablas y gráficos.
