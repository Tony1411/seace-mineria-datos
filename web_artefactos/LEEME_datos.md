# Contrato de datos para la página web
**Módulos de textos similares (MinHash y LSH) y vecinos más cercanos (ANN)**

Esta carpeta trae todo lo que la página necesita de esos módulos: archivos **JSON** ya calculados y un texto en Markdown por módulo.
La página **no necesita Spark ni Python**: solo lee estos archivos (arquitectura "calcular una vez, explorar muchas" del enunciado).

```
web_artefactos/
  LEEME_datos.md              (este archivo)
  similitud/
    minhash_error.json        error de MinHash según el número de hashes
    minhash_pares.json        pares de textos: Jaccard exacto y estimado
    lsh_grid.json             LSH: bandas y filas frente a precisión y recall
    lsh_resumen.json          LSH aplicado a todos los textos
    casos_similares.json      60 pares casi iguales (20 por tipo)
    grupos_repetidos.json     100 textos que más se repiten
    metadata.json             parámetros y tamaños
    texto_similitud.md        texto del módulo (pregunta, pipeline, interpretación, límites)
  ann/
    ann_curvas.json           recall y tiempo según el parámetro de IVF y de HNSW
    ann_ejemplos.json         20 consultas con vecinos exactos y aproximados
    ann_resumen.json          tiempos de construcción y tamaños de los índices
    texto_ann.md              texto del módulo
```
Todo pesa menos de 1 MB en total (el archivo más grande es `minhash_pares.json`, 328 KB).

## 1. Cómo cargar los archivos
```javascript
// con D3
const d = await d3.json("similitud/lsh_grid.json");
// con JavaScript solo (sirve para Chart.js, Plotly, etc.)
const d = await (await fetch("similitud/lsh_grid.json")).json();

d.meta   // qué es el archivo (título, descripción, campos, parámetros)
d.datos  // los datos
```
**Importante:** `fetch` y `d3.json` **no funcionan si abres el HTML con doble clic** (`file://`). Usa un servidor local (`python -m http.server` en la carpeta de la página) o publícala (por ejemplo en GitHub Pages).

## 2. Formato común
- Cada JSON tiene dos partes: **`meta`** (describe el archivo y explica cada campo) y **`datos`**.
- `datos` es casi siempre una **lista de registros**. La excepción es `minhash_error.json`, donde `datos` es un objeto con `global` y `por_tramo`.
- Los números son números (no texto). Las fechas van en formato `AAAA-MM-DD`. Las proporciones (precisión, recall, Jaccard) van entre 0 y 1.
- Los nombres de los campos están en español, sin tildes.
- Los textos de los procesos están **normalizados** (minúsculas, sin tildes ni signos).

## 3. Módulo MinHash
**Pregunta:** ¿cuánto error tiene MinHash al estimar el Jaccard, según cuántas funciones hash se usen?
**Control sugerido:** selector de **k** con los valores **8, 16, 32, 64 y 128**.

| Archivo | Contenido |
|---|---|
| `minhash_error.json` → `datos.global` | Una fila por k: `k`, `error_medio`, `rmse`, `error_p95` |
| `minhash_error.json` → `datos.por_tramo` | Una fila por k y tramo de Jaccard: `k`, `tramo_jaccard` (por ejemplo `"0.4-0.5"`), `error_medio`, `n_pares` |
| `minhash_pares.json` → `datos` | 2,759 pares: `jaccard_exacto` y `est_k8`, `est_k16`, `est_k32`, `est_k64`, `est_k128` (Jaccard estimado con ese k) |

**Gráficos posibles:**
- Dispersión `jaccard_exacto` (eje x) contra `est_kN` (eje y) con la diagonal. Al subir k los puntos se acercan a la diagonal.
- Error contra k, con la curva teórica dibujada encima.

**Calcular en vivo en JavaScript:** error estándar teórico = `Math.sqrt(s * (1 - s) / k)`, donde `s` es el Jaccard. Sirve para cualquier k, no solo los precalculados.

## 4. Módulo LSH
**Pregunta:** ¿cómo cambian los falsos positivos y los falsos negativos según las bandas (b) y las filas (r)?
**Controles sugeridos:** selector de **(bandas, filas)** y selector de **umbral** (0.5, 0.6, 0.7, 0.8, 0.9).

**`lsh_grid.json` → `datos`** (50 filas = 10 combinaciones x 5 umbrales):

| Campo | Qué es |
|---|---|
| `bandas`, `filas` | b y r. Las combinaciones son (128,1), (64,2), (42,3), (32,4), (25,5), (21,6), (16,8), (12,10), (10,12) y (8,16) |
| `n_hashes` | b x r: cuántos números de la firma se usan (máximo 128) |
| `umbral_efectivo` | aproximadamente `(1/b)^(1/r)` |
| `umbral` | Jaccard mínimo para considerar "similar" un par |
| `candidatos` | pares que coinciden en alguna banda |
| `tp` | candidatos realmente similares |
| `fp` | candidatos que no lo son (**falsos positivos**) |
| `fn` | pares similares que no fueron candidatos (**falsos negativos**) |
| `precision` | `tp / candidatos` |
| `recall` | `tp / pares verdaderos del umbral` |

`meta.pares_verdaderos_por_umbral` trae cuántos pares similares hay por umbral: `{"0.5": 7599, "0.6": 3906, "0.7": 1569, "0.8": 647, "0.9": 59}`.

**Calcular en vivo en JavaScript** (sirve para **cualquier** b y r, no solo las precalculadas):
```javascript
const probCandidato = (s, b, r) => 1 - Math.pow(1 - Math.pow(s, r), b);  // curva en S
const umbralEfectivo = (b, r) => Math.pow(1 / b, 1 / r);
```
Gráfico sugerido: curva en S de la combinación elegida, con una línea vertical en el umbral, y al lado la tabla de precisión, recall, falsos positivos y falsos negativos medidos.

**`lsh_resumen.json` → `datos[0]`:** resultado de aplicar LSH (21 bandas x 6 filas) a los 163,208 textos: `candidatos` (693,144), `pares_posibles` (13,318,344,028), `fraccion_comparada` y los pares encontrados por umbral (`similares_50` ... `similares_90`).

## 5. Módulo de casos y textos repetidos (estático, con filtros)
**`casos_similares.json` → `datos`** (60 pares: 20 de cada tipo):

| Campo | Qué es |
|---|---|
| `tipo_caso` | `misma_entidad`, `mismo_departamento` o `departamentos_distintos` |
| `jaccard` | similitud exacta (entre 0.8 y 1, sin incluir los idénticos) |
| `texto_a`, `texto_b` | los dos textos. La página puede resaltar las palabras que difieren |
| `entidad_a`, `entidad_b`, `departamento_a`, `departamento_b` | entidad contratante y su departamento |
| `primera_fecha_a`, `primera_fecha_b` | primera publicación del texto |
| `n_procesos_a`, `n_procesos_b` | procesos con ese texto |

**Ojo:** es una muestra **balanceada**, no proporcional. En los datos reales, entre los pares cuyos textos pertenecen a una sola entidad, el 96.6% es de tipo `misma_entidad`. No la uses para mostrar porcentajes.

**`grupos_repetidos.json` → `datos`** (100 textos): `texto`, `n_procesos`, `n_entidades`, `n_departamentos`, `entidad` (la que más lo usa), `departamento`, `primera_fecha`, `ultima_fecha`, `valor_total_pen`. Sirve para un gráfico de barras de los más repetidos.

## 6. Módulo ANN (vecinos más cercanos)
**Pregunta:** ¿cuánto se pierde en precisión, y cuánto se gana en tiempo, al buscar vecinos de forma aproximada?
**Control sugerido:** selector de método (IVF o HNSW) y deslizador del parámetro.

**`ann_curvas.json` → `datos`** (14 filas): `metodo` (`IVF` o `HNSW`), `parametro` (`nprobe` o `efSearch`), `valor`, `recall_10`, `ms_por_consulta`, `veces_mas_rapido`.
- Valores de IVF: `nprobe` = 1, 2, 4, 8, 16, 32, 64, 128.
- Valores de HNSW: `efSearch` = 8, 16, 32, 64, 128, 256.
- `meta.exacta` trae la referencia: búsqueda exacta, recall 1.0 y sus milisegundos por consulta.

Gráfico sugerido: recall (eje y) contra milisegundos (eje x, escala logarítmica), una línea por método y una línea vertical para la búsqueda exacta.

**`ann_ejemplos.json` → `datos`** (20 consultas): `consulta` (texto), `vecinos_exactos` y `vecinos_hnsw` (listas de 5 objetos con `texto` y `similitud`), `coinciden_en_top5` (cuántos de los 5 coinciden).

**`ann_resumen.json` → `datos`:** 4 registros con campos distintos (uno por método y uno de la representación). Cada uno trae `metodo`, y los tiempos de construcción (`construccion_s`) y tamaños (`indice_mb`) donde aplica.

## 7. Textos de cada módulo
`texto_similitud.md` y `texto_ann.md` traen, para cada módulo: **pregunta de interés, pipeline, cómo leer los controles, interpretación y limitaciones**.
El enunciado pide que el análisis vaya **dentro de la página**, así que se pueden copiar tal cual al HTML. Las cifras de esos textos coinciden con los JSON.

## 8. Cosas que debes saber
- **No hay nombres de proveedores ni de postores** en ningún archivo. Solo texto del proceso, entidad, departamento, fechas y conteos.
- **Los milisegundos de ANN dependen de la máquina** donde se midieron. Lo que importa es la comparación entre métodos.
- **Reproducibilidad:** los archivos salen de los notebooks `02_similitud_minhash_lsh.ipynb` y `03_ann_ivf_hnsw.ipynb`. Usan la semilla 42, así que con los mismos datos se obtienen los mismos números. Generados con Spark 3.5.3, scikit-learn 1.8.0 y FAISS 1.15.1.
- **Si falta un campo o necesitas otro formato** (por ejemplo CSV), pídeselo a A. No edites los JSON a mano: se vuelven a generar con los notebooks.
