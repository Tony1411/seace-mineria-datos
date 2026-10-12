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
web/                  Aplicación Streamlit (app.py = menú, inicio.py = portada, pages/ = módulos)
web_artefactos/       JSON y textos precalculados (datos, similitud, ANN, discusión)
artifacts/            CSV precalculados (EDA, Bloom, CMS, DGIM, reglas)
src/streaming/        Implementaciones de Bloom filter, Count-Min Sketch y DGIM
notebooks/            Experimentos originales
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
