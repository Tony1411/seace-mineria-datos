# Análisis, discusión crítica y comunicación (Parte VI)

Responde las cinco preguntas del enunciado con los resultados de las partes I a V. Cada cifra sale de un notebook o artefacto. Las marcas dicen cuánto respaldo tiene cada dato: **(medido)** sale de una ejecución, **(estimado)** es una cuenta simple a partir de un dato medido y **(hipótesis)** es una explicación probable que no verificamos.

## 1. ¿Qué técnicas aportaron más valor y cuáles aportaron poco?

Aportaron más las técnicas que **cambiaron una decisión o descubrieron algo**.

| Técnica | Qué aportó |
|---|---|
| **EDA con Spark** | Descubrió el quiebre de 2025: abril tiene 9,356 procesos y mayo 3,646. Coincide con la Ley 32069 y obliga a separar "antes" y "después". **De lo más importante.** |
| **Similitud (MinHash, LSH)** | El 96.6% de los pares casi iguales ocurre dentro de la misma entidad. Un texto genérico se repite en 550 procesos de una entidad. **De lo más importante.** |
| **Reglas (FP-Growth)** | `postores=0` sube DESIERTO de 12.88% a 35.45% (lift 2.75). Municipalidad con cero postores lleva NULO a 59.5% (lift 9.8). **Pistas útiles, pero varias reglas son triviales:** 9,110 de 33,804 |
| **DGIM** | Estima los desiertos recientes con 9% a 12% de error. **Medida descriptiva; no cambió conclusiones.** |
| **ANN (IVF, HNSW)** | Es infraestructura de búsqueda, no un hallazgo. **Aportó la comparación:** HNSW funcionó bien e IVF no. |
| **Bloom y Count-Min Sketch** | Con 226,293 postores, un `set` y un `dict` caben en memoria (**estimado:** ~19 y ~25 MiB). **Aportaron poco aquí.** Su valor es mostrar el compromiso entre memoria y precisión. |

## 2. ¿Cuánto se pierde en precisión con los métodos aproximados y vale la pena?

| Técnica | Qué se pierde (medido) | Qué se gana | ¿Vale la pena? |
|---|---|---|---|
| **MinHash, 128 hashes** | Error medio 0.027 (el 95% falla menos de 0.070) | Firma de tamaño fijo | **Sí, como puente a LSH.** Por sí solo no ahorra memoria |
| **LSH, 21×6** | 17 de 1,569 pares (recall 0.989, en EsSalud) | Revisa 693,144 pares: el 0.005% de 13,318,344,028 | **Sí, imprescindible** |
| **HNSW, efSearch 16** | 3.9% de los vecinos (recall 96.1%) | 20 veces más rápido (0.097 contra 1.91 ms) | **Depende del volumen** |
| **IVF** | `nprobe=1`: solo 56.7%. `nprobe=128`: 91.6% | Con `nprobe≥64` ya es más lento que la búsqueda exacta | **No con estos vectores** |
| **Bloom, 10 bits** | 0.12% de falsos positivos | 276 KiB contra ~19 MiB (**estimado**) | No hace falta aquí |
| **Count-Min Sketch, ancho 50,000** | Error medio 3.87; el conteo medio es 11.0. Sobreestima, nunca subestima | 977 KiB contra ~25 MiB (**estimado**) | **No aquí** |
| **DGIM** | 9% a 12% de error relativo | ~66 bytes contra 6.25 KB (**estimado**) | No hace falta aquí |

**Tres lecciones:**

1. **El costo exacto decide si conviene aproximar.** En LSH crece con el cuadrado de los textos, así que aproximar es obligatorio. En ANN la búsqueda exacta tarda 1.91 ms y HNSW tarda 89 s en construirse: solo conviene con muchas consultas.
2. **El error no es parejo.** Count-Min Sketch acierta en los postores frecuentes (el primero, 1.7% de error) y falla en los poco frecuentes: con ancho 2,719 el error medio es 416, unas 38 veces el conteo medio.
3. **La precisión de LSH baja al crecer los datos:** 22.2% en 3,493 textos y 10.3% en los 163,208 (71,424 pares reales entre 693,144 candidatos). Como cada candidato se verifica, solo cuesta tiempo.

## 3. ¿Qué tareas se beneficiaron de Spark y cuáles eran manejables en local?

**Lo medido:**

- Los CSV originales suman unos **2.7 GB** (**estimado**).
- DataFrame fue **2.8 y 2.2 veces más rápido** que RDD en dos agregaciones (1.24 contra 3.44 s, y 1.61 contra 3.62 s).
- `repartition(200)` tardó 4.13 s y `repartition(4, departamento)` 0.30 s.
- LSH sobre todos los textos: 53 s en Colab, con la verificación de 693,144 candidatos.
- Apriori local tardó 1.68 s y FP-Growth en Spark 7.73 s sobre la misma muestra, con límites de tamaño distintos.

| Tarea | ¿Spark valió la pena? |
|---|---|
| Limpieza (2.7 GB de CSV, uniones con 2.5 millones de postores) | **Sí.** Es lo más pesado |
| LSH (uniones por bandas y verificación de pares) | **Sí** (**hipótesis:** en local sería más lento; no lo medimos) |
| EDA (209,740 procesos) | **Dudoso.** Probablemente cabe en pandas (**hipótesis**) |
| Reglas (196,158 transacciones) | **Dudoso.** Apriori local ganó en tiempo |
| Bloom, Count-Min Sketch y DGIM | **No aplica.** Son procesos secuenciales en Python puro |

**Limitación:** todo Spark corrió en modo `local[*]`, una sola máquina. Muestra el modelo de programación, pero **no mide rendimiento en un clúster**.

## 4. ¿Cómo cambiarían los resultados y las decisiones con 10 o 100 veces más datos?

Las cifras de 10× y 100× son **extrapolaciones lineales** (estimado), no mediciones.

| Componente | Hoy (medido) | Con 10× | Con 100× | Decisión |
|---|---|---|---|---|
| **Limpieza y EDA** | ~2.7 GB | ~27 GB | ~270 GB | Spark pasa a ser **necesario**. Lima reúne el 30% de los procesos, así que las particiones quedan desiguales |
| **Pares de textos** | 13,318,344,028 | ~1.3 billones | ~133 billones | **LSH obligatorio** y reajustar bandas y filas, porque los falsos positivos crecen |
| **ANN exacta** | 1.91 ms; 334 MB | ~19 ms; 3.3 GB | ~191 ms; 33 GB | Ya conviene un índice. HNSW pesaría ~3.8 y ~38 GB |
| **Bloom Filter** | 276 KiB | ~2.7 MB | ~27 MB | El `set` exacto sería ~190 MiB y ~1.9 GB: **ahí sí conviene** |
| **Count-Min Sketch** | 977 KiB | — | — | El error crece con el total de eventos: habría que **ampliar el ancho** |
| **DGIM** | ~66 bytes | casi igual | casi igual | Es la técnica que **mejor escala** |
| **Reglas** | 5,002 conjuntos (soporte 1%) | — | — | El tiempo crece al bajar el soporte (de 472 a 11,351 conjuntos entre 5% y 0.5%). A 100×, FP-Growth en Spark sería necesario |

## 5. ¿Qué implicancias tiene aplicar estas técnicas sobre datos públicos peruanos?

**Aporte:** los datos son públicos (OECE, CC BY 4.0), así que cualquiera puede reproducir el análisis. Las técnicas ayudan a **priorizar** dónde mirar: textos repetidos, procesos sin postores, concentración territorial.

**Riesgos y qué hacemos:**

| Riesgo | Qué hacemos |
|---|---|
| **Confundir parecido con irregularidad.** Un texto casi igual puede ser una plantilla o una compra recurrente | Decimos que no prueba irregularidad. Para hablar de fraccionamiento harían falta monto, fecha y proveedor |
| **Nombrar entidades.** Los ejemplos podrían leerse como acusaciones | Se presentan como ejemplos del patrón, no como sospechas |
| **Tomar un dato registrado como un hecho.** `postores=0` no es necesariamente ausencia de competencia. El 78% de los montos en cero son procesos con información protegida | Se marcan como "valor no disponible" y se explica |
| **Variables y cobertura aproximadas.** `entidad_tipo` es una heurística (23% queda como `otro`), el departamento es la sede y solo hay procedimientos de selección | Se documentan. Los resultados describen esos procedimientos, no toda la compra pública |
| **Datos personales.** Algunos postores son personas naturales (RUC que empieza con 10) | Se muestran solo agregados y se **enmascaran los RUC de personas naturales** |

**Uso recomendado:** seleccionar casos que **una persona revisará**, no acusar. Los hallazgos orientan una auditoría, no la concluyen.

## 6. Limitaciones metodológicas del proyecto

1. **La igualdad entre Apriori y FP-Growth dio `False`, y la causa no está comprobada.** Sí se comparó: 1,969 itemsets de Apriori contra 2,005 de FP-Growth sobre la misma muestra. La causa probable es que Apriori tiene un límite de 5 ítems y FP-Growth no (**hipótesis**). Para comprobarla hay que comparar solo los tamaños 5 o menos.
2. **La comparación antes y después de la ley está incompleta.** Las reglas finales no separan bien los dos periodos.
3. **Las reglas 7 a 12 de las seleccionadas son casi tautológicas.** La página muestra solo las 6 primeras.
4. **LSH:** el recall se midió solo en el subconjunto de EsSalud.
5. **ANN:** TF-IDF compara palabras, no significado. Una consulta de "sistema de sonido" tiene como primer vecino una compra de equipos de cómputo (0.70) porque comparten la frase de plantilla. Por qué IVF funciona mal es una **hipótesis**.
6. **Tiempos:** una sola corrida, en entornos distintos y en una sola máquina. Sirven para comparar métodos dentro de una parte, no entre partes.
7. **Cortes de datos:** los estados son al 3 de septiembre de 2026. Los procesos recientes están más abiertos (CONVOCADO: 13.5% en 2026 contra 4.7% en 2024).

## 7. ¿Qué técnica usar en cada caso?

| Si el problema es... | Usar | Cuidado |
|---|---|---|
| Encontrar textos casi iguales entre cientos de miles | **Shingles + MinHash + LSH** | Elegir bandas y filas según qué es más caro: perder pares o revisar de más |
| Buscar vecinos de un texto muchas veces | **HNSW** | Construir el índice cuesta; con pocas consultas no se recupera |
| Saber si algo "ya apareció" con poca memoria | **Bloom Filter** | A pocos millones de elementos basta un `set` |
| Estimar frecuencias de elementos muy repetidos | **Count-Min Sketch** | Falla con los poco frecuentes |
| Contar eventos en una ventana reciente de un flujo | **DGIM** | Error de ~10% |
| Encontrar combinaciones frecuentes | **FP-Growth** | Filtrar reglas triviales y no leer el lift como causa |
| Limpiar y unir tablas de varios GB | **Spark** | Con pocos cientos de miles de filas, el costo extra no se paga |
