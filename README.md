# SEACE: minería de datos en grande sobre contrataciones públicas del Perú

Proyecto Integrador de Data Mining (UTEC) — Prof. Heider Sanchez.
Datos: contrataciones públicas del SEACE en formato OCDS (OECE), enero 2024 a agosto 2026.

**Integrantes:** Anthony Roca · Willian Berrocal · Jimena Mamani
**Página web:** https://seace-mineria.streamlit.app/

## ¿De qué trata?
Una contratación pública deja mucho rastro: miles de procesos, textos de ítems, postores y adjudicaciones.
Usamos técnicas de minería de datos a gran escala (Spark local, sketches de streaming, búsqueda de similares y reglas de asociación) para responder preguntas concretas y **medir qué se pierde al aproximar**.

Ninguna técnica de este proyecto prueba irregularidades. Un texto parecido, una regla o un postor frecuente son **pistas para revisar**, no acusaciones.

## Datos en cifras
| Qué | Valor |
|---|---|
| Filas leídas del CSV | 357,729 |
| Procesos finales (tras limpieza) | 209,740 |
| Entidades | 2,992 |
| Postores (registros) | 2,493,612 |
| Textos de ítems únicos analizados | 163,208 |
| Periodo | 2024-01 a 2026-08 |

La limpieza completa (embudo, decisiones, calidad y límites) está en la página **Datos, KDD y limpieza** y en `web_artefactos/datos/reporte_calidad.json`.

## Preguntas de interés
1. **¿Cambió algo en los procesos tras la Ley 32069?** Los procesos pasaron de 9,356 en abril de 2025 a 3,646 en mayo de 2025; la ley rige desde el 22-04-2025.
2. **¿Hay textos repetidos o plantillas, y se pueden buscar los más parecidos rápido?** MinHash + LSH sobre 163,208 textos; ANN con HNSW.
3. **¿Qué tan recurrentes y concentrados son los postores, usando poca memoria?** 90.9% son reapariciones; el top-10 concentra 2.7%.
4. **¿Qué procesos terminan desiertos o nulos y por qué?** Con 0 postores, DESIERTO sube de 12.88% a 35.45% (lift 2.75).
5. **¿Cuánta precisión se pierde al aproximar?** Ver la tabla de resultados.

## Resultados principales (todos medidos en los notebooks)
| Técnica | Resultado | Notebook |
|---|---|---|
| MinHash (128 hashes) | Error medio 0.027, p95 0.070 | `B_01.1` |
| LSH (21 bandas × 6 filas) | Recall 0.989 en subconjunto. 693,144 candidatos = 0.005% de 13,318,344,028 pares. Precisión 10.3% sobre todos los textos | `B_01.1` |
| ANN IVF y HNSW frente a la búsqueda exacta (HNSW ef=16) | Recall 96.1%, unas 20× más rápido (0.097 ms vs 1.91 ms). IVF fue más lento que la búsqueda exacta desde nprobe 64 | `B_01.2` |
| Bloom filter (10 bits/elem) | Falsos positivos 0.12%, 276 KiB frente a ~19 MiB de un set | `B_03` |
| Count-Min Sketch (w=50,000) | Error absoluto medio 3.87 (la media real es 11.02); con w=2,719 sube a 416 | `B_04` |
| DGIM | Error relativo 9–12%, unos 66 bytes teóricos para W=50,000 | `B_05` |
| Reglas de asociación | 33,804 reglas, 9,110 triviales. Con municipalidad y 0 postores, NULO llega a 59.5% (lift 9.8) | `C_Parte5` |
| Spark | RDD fue 2.8× y 2.2× más lento que DataFrame en las dos agregaciones; `repartition(200)` 4.13 s vs `repartition(4, dep)` 0.30 s | `C_Parte5` |

La discusión crítica (valor, pérdida por aproximar, Spark vs local, escala 10×/100×, implicancias y limitaciones) está en la página **Discusión crítica** y en `web_artefactos/discusion/discusion_critica.md`.

## Estructura del repositorio
```
web/                  Aplicación Streamlit (app.py = menú, inicio.py = portada, pages/ = módulos; utils_p2.py lee los resultados del Proyecto 2)
web_artefactos/       JSON y textos precalculados (datos, similitud, ANN, discusión); p2/ = 31 resultados del Proyecto 2
artifacts/            CSV precalculados (EDA, Bloom, CMS, DGIM, reglas)
src/streaming/        Implementaciones de Bloom filter, Count-Min Sketch y DGIM
notebooks/            B_* y C_* = Proyecto 1; P2_01 a P2_06 = Proyecto 2
requirements.txt      Dependencias solo de la web
requirements-notebooks.txt  Dependencias para reproducir los notebooks
```

## Cómo ejecutar la página
La página **no ejecuta Spark**: solo lee los resultados ya calculados ("calcular una vez, explorar muchas").
```bash
python -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run web/app.py
```
Python 3.11 o superior. El equipo usó 3.14 y la web se probó también en 3.13.

## Módulos de la página
Cada hallazgo es un módulo con su pregunta de interés, visualización, interpretación escrita y, donde aplica, controles en vivo.

| Módulo (`web/pages/`) | Parte | Controles en vivo |
|---|---|---|
| Datos, KDD y limpieza | I | (texto, embudo y calidad; con cita de la fuente) |
| EDA | I | año y métrica |
| Spark y particiones | I | estadístico (mínimo o mediana) |
| MinHash y LSH | II | número de hashes, bandas × filas y umbral |
| Casos de textos | II | tipo de caso, umbral de Jaccard y cuántos mostrar |
| ANN | III | método (IVF o HNSW) y su parámetro (nprobe o efSearch) |
| Bloom filter | IV | bits por elemento y número de hashes |
| Count-Min Sketch | IV | ancho y profundidad |
| DGIM | IV | tamaño de la ventana |
| Reglas de asociación | V | soporte, confianza y lift mínimos; consecuente; ocultar reglas triviales |
| Apriori y FP-Growth | V | soporte mínimo |
| Discusión crítica | VI | (texto: valor de cada técnica, escala, implicancias y limitaciones) |

Hay más de tres hallazgos con parámetros ajustables en vivo (LSH, ANN, Bloom, Count-Min Sketch, DGIM y reglas).

## Cómo reproducir los notebooks
1. Descargar los datos del SEACE/OCDS (ver "Fuente y licencia"). Los datos crudos (≈2.7 GB en CSV) y los Parquet **no están en el repositorio**.
2. Instalar `requirements-notebooks.txt`.
3. Ejecutar en este orden:

| Notebook | Entorno | Motor | Por qué | Artefactos que exporta |
|---|---|---|---|---|
| `B_00_Limpieza` | Laptop | Spark local | Lee y une ~2.7 GB de CSV (incluye 2.5 millones de participaciones); Spark trabaja por columnas y en paralelo | 6 tablas Parquet y `web_artefactos/datos/reporte_calidad.json` |
| `B_01_EDA_Spark` | Laptop | Spark local | Agregaciones sobre los Parquet | `artifacts/eda/*.csv` |
| `B_01.1_similitud_minhash_lsh_final` | Colab | Spark local + Python | LSH con uniones por bandas en Spark (lo pide la tarea); el resto es Python | `web_artefactos/similitud/*.json` |
| `B_01.2_ann_ivf_hnsw_final` | Colab | Local (FAISS, scikit-learn) | Los índices IVF y HNSW viven en la memoria de una sola máquina; Spark no aporta | `web_artefactos/ann/*.json` |
| `B_02_Flujo` | Laptop | Spark para leer y ordenar; Python puro | Ordena por fecha de publicación para simular el flujo | prepara el flujo para B_03 a B_05 |
| `B_03_Bloom_Filter` | Laptop | Python puro | Un sketch procesa un evento a la vez, en orden: es secuencial | `artifacts/bloom/*.csv` |
| `B_04_Count_Min_Sketch` | Laptop | Python puro | Igual: procesamiento secuencial del flujo | `artifacts/cms/*.csv` |
| `B_05_DGIM` | Laptop | Python puro | Igual: procesamiento secuencial del flujo | `artifacts/dgim/*.csv` |
| `C_Parte5_Reglas_Asociacion` | Colab | Spark (RDD, DataFrame, FP-Growth) y Apriori con NumPy | FP-Growth de Spark MLlib sobre 196,158 transacciones; la comparación RDD frente a DataFrame es parte de la tarea | `artifacts/c/*` |

Todo Spark corre en modo `local[*]`, no en un clúster.

Los artefactos exportados son lo único que lee la página (`web/`): ella no ejecuta Spark.

Rutas que debes ajustar:
- Los notebooks `B_*` usan `Path.home() / "dm"`. Cambia `PROJECT_ROOT` a tu carpeta.
- Los notebooks `B_01.1`, `B_01.2` y `C_*` usan `/content/drive/...` (Google Drive en Colab).

## Proyecto Integrador 2: grafos, clustering y aprendizaje de representación
Continúa el proyecto con las Partes I, II y III de la guía del Proyecto 2, sobre los mismos Parquet. Se **agregan** 6 notebooks (`P2_*`), 31 archivos de resultados (`web_artefactos/p2/`) y 6 módulos de la página. Lo anterior no se modificó; solo se amplió el menú (`web/app.py`) y las dependencias de los notebooks.

**Preguntas de interés**
1. **¿Qué tipos de proveedores existen según cómo contratan con el Estado, y cuáles se salen de su tipo?** Tres tipos: *no ganan* (51%), *ganan poco* (37%) y *activos en varias entidades* (13%); con k = 5 se afinan en cinco grupos (por ejemplo, entre los que no ganan se separan los que «pasaron de largo», 4 meses activos, de los que «insisten», 20 meses). Se salen del tipo los proveedores muy grandes y generalistas (por ejemplo, 1,427 adjudicaciones con 262 entidades); de 30 casos extremos, 29 son de ese tipo.
2. **¿Qué proveedores son sustitutos entre sí para una misma entidad o categoría, y qué afinidades entidad–proveedor son inusuales?** Los proveedores parecidos por contenido comparten entidad en 52.4% de los casos (al azar: 2.8%) y se presentan a los mismos procesos en 38.7% (al azar: 1.4%). Las afinidades inusuales (843 pares, 2% de 42,163) son sobre todo servicios de apoyo en entidades que compran otras cosas.
3. *(Partes IV–VI, siguiente etapa)* Qué actores concentran el mercado y qué comunidades forman. Aquí solo se construye el grafo de co-participación (Parte I).

Todo es una **señal descriptiva para revisar**, no una acusación.

**Resultados principales**
| Qué | Resultado | Notebook |
|---|---|---|
| Universo entidad × proveedor | 9,833 proveedores × 2,331 entidades; 44,205 pares en train; densidad 0.19%. Corte 2026-03-01. Consorcios (RUC de 7 dígitos, 21.8% de las adjudicaciones) fuera | `P2_01` |
| Grafo de co-participación | 40,106 proveedores y 1,482,754 aristas (peso ≥ 2, tope 30 postores); 99.2% en un solo bloque conectado | `P2_02` |
| Clustering de proveedores | K-Means k = 5 (el codo de la inercia se frena con fuerza después de 5; silueta 0.462, igual que con k = 4; estabilidad ARI 0.98, la de k = 4 es la más baja entre 3 y 6, 0.93). En entidades k = 6, pero con silueta (0.25) y estabilidad (0.80) bajas: son tendencias. Los casos extremos se buscan en todos los puntos. DBSCAN/HDBSCAN y jerárquico muestran un núcleo denso y dos grandes bloques | `P2_03` |
| Recomendador por contenido | TF-IDF + proyección a 512 + HNSW (recall@10 98.8% frente a exacta); recall@10 en test 0.080 | `P2_04` |
| Recomendador colaborativo | ALS (128 factores, regularización 1, alpha 10) recall@10 en test 0.136 (intervalo 95%: 0.121 a 0.151; 5 semillas: 0.137 ± 0.002) frente a 0.022 de «populares»; vecindario user–user (K = 50) 0.119 y item–item (K = 800) 0.083. User–user gana porque acierta con proveedores grandes (46% de su top-10 son los 100 más populares). Las rejillas se ampliaron hasta que los mejores valores quedaron dentro | `P2_05`, `P2_06` |
| Híbrido | Con α elegido en validación (0.1, el mismo en tres cortes): 0.111, no supera a ALS solo (diferencia creíble); en el test el mejor α sería ≈ 0.6 (0.152), pero eso no se usó para elegir. Los proveedores de la validación tienen menos historia que los del test (mediana 4 frente a 6 entidades) | `P2_06` |

**Notebooks nuevos** (ejecutar en este orden; todos leen los Parquet del Proyecto 1 o los que deja el notebook anterior)
| Notebook | Motor | Por qué | Artefactos que exporta (`web_artefactos/p2/`) |
|---|---|---|---|
| `P2_01_Base_Relacional` | Spark local | Une y agrega millones de filas; prueba de particionamiento | `reporte_base.json` |
| `P2_02_Grafo_Coparticipacion` | Spark local + SciPy | La auto-unión de postores por proceso es grande | `grafo_umbrales.csv`, `grafo_grado.csv`, `grafo_resumen.json` |
| `P2_03_Clustering` | scikit-learn + SciPy | Tablas chicas (miles de filas) en una sola máquina | `pca_varianza.csv`, `kmeans_k.csv`, `kmeans_estabilidad.csv`, `kmeans_perfiles.csv`, `puntos.csv`, `dbscan_grid.csv`, `dbscan_kdist.csv`, `dendrograma.json`, `outliers.csv` |
| `P2_04_Recomendador_Contenido` | scikit-learn + FAISS | Índice HNSW en memoria | `contenido_ejemplos.json` |
| `P2_05_Recomendador_Colaborativo` | NumPy + Spark MLlib (ALS) | ALS es la parte que pide Spark | `vecindario_k.csv`, `vecindario_user_k.csv`, `vecindario_variantes.csv`, `als_parametros.csv`, `als_alpha.csv` |
| `P2_06_Evaluacion_Hibrido` | NumPy + Spark MLlib | Evalúa en el test (con intervalos, semillas y cobertura), elige α con tres cortes, sustitutos y afinidades | `eval_resultados.csv`, `eval_ic.csv`, `eval_diferencias.csv`, `cobertura.csv`, `als_semillas.csv`, `diagnostico_grado.csv`, `reporte_evaluacion.json`, `hibrido_alfa.csv`, `sustitutos.json`, `sustitutos_categoria.csv`, `afinidades_inusuales.csv`, `ejemplos_recomendaciones.json` |

Las rutas se leen de variables de entorno (`P2_PARQUET`: Parquet del Proyecto 1; `P2_DATOS`: tablas intermedias que van dejando los notebooks; `P2_WEB`: salida para la página). Si no existen, usan carpetas de Google Drive como en Colab. Las tablas intermedias (Parquet y `.npy`) **no están en el repositorio**: se regeneran ejecutando los notebooks en orden.

| Módulo nuevo (`web/pages/`) | Parte | Controles en vivo |
|---|---|---|
| Base relacional | I | (embudo, universo y particiones) |
| Grafo de co-participación | I | peso mínimo de las aristas |
| Clustering | II | proveedores o entidades, k, `eps`, `min_samples` y tamaño mínimo de grupo (con gráfico de estabilidad y de k-distancias) |
| Recomendador por contenido | III | entidad de ejemplo |
| Recomendador colaborativo | III | vecinos (K) en item–item y user–user, factores y regularización |
| Evaluación e híbrido | III | top-k, métrica, α, proveedor, tipo de entidad y monto mínimo |

**Datos personales:** igual que arriba, los RUC que no empiezan con 20 se muestran enmascarados y el nombre de una persona natural se reemplaza por «Persona natural (RUC 10283****79)».

**Limitaciones del Proyecto 2**
- Los consorcios se dejaron fuera: un proveedor que gana solo dentro de consorcios aparece como «no gana».
- El test cubre pocos meses (desde 2026-03-01); las métricas pueden cambiar con más datos.
- El peso del híbrido elegido en validación no coincidió con el mejor en el test (ver `P2_06`).
- Los grupos de entidades son poco estables (ARI ≈ 0.80); es una sola partición temporal, así que los intervalos miden el azar al elegir entidades, no el cambio de periodo.
- Las afinidades inusuales y los casos extremos tienen explicaciones normales frecuentes (servicios de apoyo, pocos procesos).

## Fuente y licencia
- Fuente: datos abiertos de contrataciones públicas del Perú (SEACE) en formato OCDS, publicados por la OECE a través de la Open Contracting Partnership.
- Licencia: CC BY 4.0.
- Los datos fueron **modificados** por nosotros (limpieza, filtro de periodo, tablas derivadas).
- Datos obtenidos por última vez: 4 de septiembre de 2026 (última actualización de la fuente: 3 de septiembre de 2026).
- Cita sugerida: ver la página **Datos, KDD y limpieza**.

## Datos personales
Algunos proveedores son personas naturales. Por eso:
- Los RUC de persona natural se muestran enmascarados (`10283****79`).
- Se omitió un nombre de paciente que aparecía en un texto de ítem.
- Los RUC que empiezan con 20 (personas jurídicas) se muestran completos.

## Limitaciones
- Los resultados dependen de un solo periodo (2024-01 a 2026-08) y de la calidad del dato publicado.
- LSH tiene baja precisión en el total (10.3%): genera candidatos que hay que verificar.
- Las reglas de asociación incluyen reglas triviales (9,110). De las 12 seleccionadas, 6 son casi tautológicas y la web solo muestra las otras 6.
- No se probó un clúster real. Las conclusiones de escala (10×, 100×) son **estimaciones** y están marcadas como tales.
- La comparación antes y después de la ley dentro de las reglas de asociación quedó abierta.
- La comparación de igualdad entre Apriori y FP-Growth dio `False` (1,969 vs 2,005 itemsets). La causa probable es el límite de 5 ítems de Apriori (hipótesis, aún sin comprobar; ver la página **Apriori y FP-Growth** de la web).
