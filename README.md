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
web_artefactos/       JSON y textos precalculados (datos, similitud, ANN, discusión); p2/ = 58 resultados del Proyecto 2
artifacts/            CSV precalculados (EDA, Bloom, CMS, DGIM, reglas)
src/streaming/        Implementaciones de Bloom filter, Count-Min Sketch y DGIM
notebooks/            B_* y C_* = Proyecto 1; P2_01 a P2_09 = Proyecto 2
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
Continúa el proyecto con las Partes I a VII de la guía del Proyecto 2, sobre los mismos Parquet. Se **agregan** 9 notebooks (`P2_*`), 58 archivos de resultados (`web_artefactos/p2/`) y 10 módulos de la página. Las Partes I a III se construyeron primero; las Partes IV a VII se agregaron después sin modificar lo anterior, salvo el menú (`web/app.py`), la portada (`web/inicio.py`), los enlaces «Siguiente» de dos páginas y las dependencias de los notebooks.

**Preguntas de interés**
1. **¿Qué tipos de proveedores existen según cómo contratan con el Estado, y cuáles se salen de su tipo?** Tres tipos: *no ganan* (51%), *ganan poco* (37%) y *activos en varias entidades* (13%); con k = 5 se afinan en cinco grupos (por ejemplo, entre los que no ganan se separan los que «pasaron de largo», 4 meses activos, de los que «insisten», 20 meses). Se salen del tipo los proveedores muy grandes y generalistas (por ejemplo, 1,427 adjudicaciones con 262 entidades); de 30 casos extremos, 29 son de ese tipo.
2. **¿Qué proveedores son sustitutos entre sí para una misma entidad o categoría, y qué afinidades entidad–proveedor son inusuales?** Los proveedores parecidos por contenido comparten entidad en 52.4% de los casos (al azar: 2.8%) y se presentan a los mismos procesos en 38.7% (al azar: 1.4%). Las afinidades inusuales (843 pares, 2% de 42,163) son sobre todo servicios de apoyo en entidades que compran otras cosas.
3. **¿Qué actores concentran el mercado, qué comunidades forman y cómo se representa a cada proveedor?** *(Partes IV a VI)* El 1% de proveedores con más PageRank (431) reúne 16.7% del total; el ranking de arriba casi no cambia entre β = 0.50 y 0.95. Louvain encuentra 135 comunidades en 40,106 proveedores (Q = 0.65; 22 con al menos 10 proveedores), separadas sobre todo por **rubro** (bienes, servicios u obras) y menos por región. Con SVD y con node2vec, entre 91% y 93% de los 10 vecinos más cercanos de un proveedor está en su misma comunidad (12% al azar); los embeddings no coinciden con los tipos de la Parte II (ARI ≈ 0): son dos miradas distintas.

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
| PageRank (Parte IV) | Grafo dirigido «A pierde frente a B» (43,115 proveedores, 508,252 aristas; 11.9% son *dead ends*). β = 0.85, 95 iteraciones; coincide con NetworkX (diferencia 2·10⁻⁹). Correlación de rangos con las victorias: 0.88. Con β de 0.50 a 0.95 (todos convergen; 0.95 necesita 295 iteraciones), 8 a 10 de los 10 primeros se mantienen | `P2_07` |
| HITS (Parte IV) | Entidades = hubs (2,331), proveedores = authorities (9,833). La autoridad coincide con el primer vector singular de la SVD (coseno 1.000). Correlación de rangos con PageRank: 0.24 (miran cosas distintas) | `P2_07` |
| Comunidades (Parte V) | Louvain sobre el grafo completo: Q = 0.648 con 135 comunidades (22 de 10 o más proveedores), en 27 s. En una muestra de 270 proveedores: Louvain Q = 0.62, Girvan–Newman 0.58 (30 comunidades), espectral 0.52 (k = 11) y LPA 0.54 a 0.59 según la semilla. Un edge betweenness en el grafo completo tardaría unas 13 horas (estimación) | `P2_08` |
| Comunidades solapadas (Parte V) | BigCLAM sobre la muestra (C = 8): 22 proveedores (8.1%) en 2 o más comunidades; ARI 0.52 frente a Louvain. La densidad entre los solapados (0.16) es menor que dentro de las comunidades (0.24), al contrario de lo visto en clase | `P2_08` |
| Embeddings (Parte VI) | Núcleo de 3,489 proveedores (≥ 120 participaciones). SVD: pureza de vecinos 0.914 y ARI 0.786 frente a Louvain; node2vec: pureza 0.929 a 0.932 y ARI 0.64 a 0.82 según p y q (sin patrón claro). Frente a los tipos de la Parte II, ARI ≈ 0 | `P2_09` |

**Notebooks nuevos** (ejecutar en este orden; todos leen los Parquet del Proyecto 1 o los que deja el notebook anterior)
| Notebook | Motor | Por qué | Artefactos que exporta (`web_artefactos/p2/`) |
|---|---|---|---|
| `P2_01_Base_Relacional` | Spark local | Une y agrega millones de filas; prueba de particionamiento | `reporte_base.json` |
| `P2_02_Grafo_Coparticipacion` | Spark local + SciPy | La auto-unión de postores por proceso es grande | `grafo_umbrales.csv`, `grafo_grado.csv`, `grafo_resumen.json` |
| `P2_03_Clustering` | scikit-learn + SciPy | Tablas chicas (miles de filas) en una sola máquina | `pca_varianza.csv`, `kmeans_k.csv`, `kmeans_estabilidad.csv`, `kmeans_perfiles.csv`, `puntos.csv`, `dbscan_grid.csv`, `dbscan_kdist.csv`, `dendrograma.json`, `outliers.csv` |
| `P2_04_Recomendador_Contenido` | scikit-learn + FAISS | Índice HNSW en memoria | `contenido_ejemplos.json` |
| `P2_05_Recomendador_Colaborativo` | NumPy + Spark MLlib (ALS) | ALS es la parte que pide Spark | `vecindario_k.csv`, `vecindario_user_k.csv`, `vecindario_variantes.csv`, `als_parametros.csv`, `als_alpha.csv` |
| `P2_06_Evaluacion_Hibrido` | NumPy + Spark MLlib | Evalúa en el test (con intervalos, semillas y cobertura), elige α con tres cortes, sustitutos y afinidades | `eval_resultados.csv`, `eval_ic.csv`, `eval_diferencias.csv`, `cobertura.csv`, `als_semillas.csv`, `diagnostico_grado.csv`, `reporte_evaluacion.json`, `hibrido_alfa.csv`, `sustitutos.json`, `sustitutos_categoria.csv`, `afinidades_inusuales.csv`, `ejemplos_recomendaciones.json` |
| `P2_07_PageRank_HITS` | Spark local + NetworkX (solo para verificar) | El grafo de derrotas sale de unir 2.4 millones de participaciones con las adjudicaciones; PageRank y HITS son iteraciones de potencia con uniones y sumas | `pr_top.csv`, `pr_por_beta.csv`, `pr_sensibilidad.csv`, `pr_convergencia.csv`, `pr_dispersion.csv`, `hits_autoridades.csv`, `hits_hubs.csv`, `hits_convergencia.csv`, `p4_resumen.json` |
| `P2_08_Comunidades` | NetworkX, NumPy y scikit-learn; Spark solo para el perfil | El grafo (1.5 millones de aristas) cabe en memoria; Girvan–Newman y espectral exigen una muestra (se mide cuánto cuesta crecer) | `com_gn_curva.csv`, `com_espectral.csv`, `com_eigenvalores.csv`, `com_escala.csv`, `com_semillas.csv`, `com_metodos.csv`, `com_resolucion.csv`, `com_lpa_completo.csv`, `com_bigclam_C.csv`, `com_perfil.csv`, `com_tamanos.csv`, `com_solapados.csv`, `p5_resumen.json` |
| `P2_09_Embeddings` | scikit-learn y gensim (local) | El núcleo (3,489 proveedores) cabe en memoria; no hace falta Spark | `emb_nodos.csv`, `emb_tsne.csv`, `emb_metricas.csv`, `emb_vecinos.csv`, `p6_resumen.json` |

Las rutas se leen de variables de entorno (`P2_PARQUET`: Parquet del Proyecto 1; `P2_DATOS`: tablas intermedias que van dejando los notebooks; `P2_WEB`: salida para la página). Si no existen, usan carpetas de Google Drive como en Colab. Las tablas intermedias (Parquet y `.npy`) **no están en el repositorio**: se regeneran ejecutando los notebooks en orden.

| Módulo nuevo (`web/pages/`) | Parte | Controles en vivo |
|---|---|---|
| Base relacional | I | (embudo, universo y particiones) |
| Grafo de co-participación | I | peso mínimo de las aristas |
| Clustering | II | proveedores o entidades, k, `eps`, `min_samples` y tamaño mínimo de grupo (con gráfico de estabilidad y de k-distancias) |
| Recomendador por contenido | III | entidad de ejemplo |
| Recomendador colaborativo | III | vecinos (K) en item–item y user–user, factores y regularización |
| Evaluación e híbrido | III | top-k, métrica, α, proveedor, tipo de entidad y monto mínimo |
| PageRank y HITS | IV | factor de amortiguamiento β y cuántos proveedores mostrar; β a comparar en la convergencia |
| Comunidades | V | resolución de Louvain (más o menos comunidades) |
| Embeddings de nodos | VI | embedding (SVD o node2vec), p, q y criterio de color del mapa t-SNE |
| Análisis y discusión (Proyecto 2) | VII | (cinco pestañas con las preguntas de la Parte VII: qué aportó más, convergencia, escala, ética y volumen mayor) |

**Datos personales:** igual que arriba, los RUC que no empiezan con 20 se muestran enmascarados y el nombre de una persona natural se reemplaza por «Persona natural (RUC 10283****79)».

**Limitaciones del Proyecto 2**
- Los consorcios se dejaron fuera: un proveedor que gana solo dentro de consorcios aparece como «no gana».
- El test cubre pocos meses (desde 2026-03-01); las métricas pueden cambiar con más datos.
- El peso del híbrido elegido en validación no coincidió con el mejor en el test (ver `P2_06`).
- Los grupos de entidades son poco estables (ARI ≈ 0.80); es una sola partición temporal, así que los intervalos miden el azar al elegir entidades, no el cambio de periodo.
- Las afinidades inusuales y los casos extremos tienen explicaciones normales frecuentes (servicios de apoyo, pocos procesos).

**Limitaciones de las Partes IV a VI**
- El grafo de PageRank usa solo procesos con hasta 30 postores y proveedores con al menos 5 participaciones; ganar un proceso no es lo mismo que ser «mejor» (influyen el precio, los requisitos y el momento). HITS usa solo la matriz de *train* (proveedores con 2 entidades o más y entidades con 3 proveedores o más).
- La sensibilidad se analiza para β entre 0.50 y 0.95 (todos convergen; β = 0.95 necesita unas 300 iteraciones). Un valor extremo como 0.99 exigiría más de mil y no se incluyó.
- Girvan–Newman y el espectral se corrieron sobre una **muestra aleatoria** de 270 proveedores; sirven para comparar métodos, no para describir el mercado. BigCLAM es una implementación simple sobre esa muestra: 90 de 270 proveedores quedan «sin comunidad» (pocas conexiones) y la observación de clase sobre la densidad en zonas de solapamiento no se cumplió.
- Los embeddings se calculan sobre un **núcleo** de los 3,489 proveedores más activos; no sirven para describir a todos. node2vec es transductivo (un vector por nodo; un proveedor nuevo exige recalcular). Con p y q se probó una sola semilla y no hay un patrón claro.
- Una comunidad o una cercanía en el embedding es una **agrupación para revisar**, no una prueba de acuerdos ni de irregularidades: proveedores del mismo rubro se encuentran en los mismos procesos de forma natural.

**Métodos que la clase solo menciona o no cubre** (se usaron de forma simple y están marcados en los notebooks)
- **HITS** (Parte IV): la clase lo nombra en las extensiones de PageRank. Se calculó con la misma iteración de potencia y se verificó contra la SVD.
- **BigCLAM** (Parte V): la clase lo deja como tema de investigación. Implementación propia en NumPy sobre un subgrafo.

Todo lo demás (SVD, node2vec con p y q, K-Means, t-SNE, Louvain, LPA, Girvan–Newman, espectral, PageRank) se vio en clase. Las caminatas de node2vec se programaron aquí porque el paquete `node2vec` no soporta bien nodos con miles de vecinos; el entrenamiento skip-gram usa `gensim`.

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
