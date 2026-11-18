import pandas as pd
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Parte VII · Análisis y discusión")

p4, p5, p6 = json_p2("p4_resumen.json"), json_p2("p5_resumen.json"), json_p2("p6_resumen.json")
g = json_p2("grafo_resumen.json")
emb = csv_p2("emb_metricas.csv")
perfil = csv_p2("com_perfil.csv")
n2v = emb[emb.embedding != "SVD"]
svd = emb[emb.embedding == "SVD"].iloc[0]
lou, bc = p5["louvain_completo_resolucion_1"], p5["bigclam"]
ari3 = p6["ari_vs_tipos_parte2"]
nucleo = p6["nucleo"]["nodos"]
p1 = perfil[perfil.resolucion == 1.0]
n_cat = int((p1.pct_categoria > 80).sum())


def ari(a, b):
    """Índice de Rand ajustado entre dos listas de etiquetas (sin depender de scikit-learn)."""
    c = pd.crosstab(pd.Series(a).values, pd.Series(b).values).to_numpy().astype(float)
    n = c.sum()
    comb = lambda x: x * (x - 1) / 2
    suma_c, suma_f, suma_k = comb(c).sum(), comb(c.sum(axis=1)).sum(), comb(c.sum(axis=0)).sum()
    esperado = suma_f * suma_k / comb(n)
    return (suma_c - esperado) / ((suma_f + suma_k) / 2 - esperado)


# Proveedores que están a la vez en el gráfico de la Parte II (muestra de 5,000) y en el núcleo de la Parte VI
pts = csv_p2("puntos.csv")
pts = pts[pts.sujeto == "proveedor"][["id", "km_5"]]
nod = csv_p2("emb_nodos.csv")[["ruc", "comunidad"]]
cruce = pts.merge(nod, left_on="id", right_on="ruc")
ari_km_lou = ari(cruce.km_5, cruce.comunidad)

encabezado(
    "¿Qué técnicas aportaron más, coinciden entre sí sus resultados, qué escaló, y qué cuidado ético exige este análisis?",
    f"Aportaron más el clustering de proveedores, el recomendador ALS, PageRank y Louvain. Los métodos que miran la **red** coinciden entre sí "
    f"(embeddings frente a Louvain: ARI {svd.ARI_vs_louvain:.2f} con SVD); los que miran **características** dan otra mirada (ARI cercano a 0). "
    f"Louvain y PageRank escalaron; Girvan–Newman, el espectral y BigCLAM exigieron una muestra. Todo es una señal para revisar, no una acusación.",
)

st.caption("Cada cifra sale de los notebooks y de los resultados del proyecto. Las valoraciones («aportó mucho», «poco») son **nuestro juicio** a partir de esas cifras.")

tab_val, tab_conv, tab_esc, tab_etica, tab_vol = st.tabs([
    "1. Qué aportó más y qué menos", "2. ¿Convergen los resultados?", "3. Qué escaló y qué exigió muestra", "4. Implicancias éticas", "5. Si el volumen fuera mayor",
])

with tab_val:
    st.success("**Respuesta corta.** Aportaron más el clustering de proveedores, ALS, PageRank y Louvain. Aportaron poco el híbrido, HITS, Girvan–Newman, el espectral y BigCLAM.")
    st.markdown("Cada fila dice qué mostró la técnica y cuánto **conocimiento nuevo** dio para responder las preguntas de interés.")
    t = pd.DataFrame([
        ("Clustering de proveedores (K-Means, Parte II)", "Tres tipos según cómo contratan (no ganan, ganan poco, activos en varias entidades); con k = 5 se afinan. De 30 casos extremos, 29 son proveedores muy grandes y generalistas.", "Mucho", "Resume el mercado en pocas etiquetas que se pueden explicar."),
        ("Recomendador ALS (Parte III)", "Recall@10 en test de 0.136, frente a 0.022 de recomendar los más populares.", "Mucho", "Es la mejora más clara sobre la referencia."),
        ("Recomendador por contenido y vecindarios (Parte III)", "Contenido 0.080; user–user 0.119; item–item 0.083.", "Medio", "Sirven como comparación y para explicar casos, pero ALS gana."),
        ("Híbrido (Parte III)", "Con α elegido en validación el recall@10 es 0.111: no supera a ALS solo.", "Poco", "Combinar no ayudó en este conjunto de datos."),
        ("PageRank (Parte IV)", f"El 1% de arriba ({p4['pagerank']['n_top1pct']} proveedores) reúne {100 * p4['pagerank']['masa_top1pct']:.1f}% del PageRank. Se parece a contar victorias ({p4['pagerank']['spearman_con_victorias']:.2f}) pero premia vencer a muchos rivales distintos.", "Mucho", "Muestra concentración y da un criterio distinto al de contar victorias."),
        ("HITS (Parte IV)", f"Los hubs se parecen al número de proveedores con que trabaja la entidad ({p4['hits']['spearman_hub_vs_n_proveedores']:.2f}).", "Poco", "Sobre todo confirma el tamaño de las entidades."),
        ("Louvain (Parte V)", f"{int(lou['comunidades'])} comunidades con Q = {lou['Q']:.2f} sobre los {p5['grafo']['nodos']:,} proveedores; en {n_cat} de las 10 comunidades más grandes, más de 80% de los miembros son del mismo rubro.", "Mucho", "Da los grupos más claros y escala."),
        ("Girvan–Newman y espectral (Parte V)", f"Q de {p5['gn']['mejor_Q']:.2f} y {p5['espectral']['mejor_Q']:.2f} en una muestra de {p5['subgrafo']['nodos']} proveedores (Louvain en la misma muestra: 0.62).", "Poco", "Sirven para aprender y comparar, pero no escalan y no mejoran a Louvain."),
        ("BigCLAM (Parte V)", f"{bc['nodos_solapados']} proveedores ({bc['pct_solapados']}%) en 2 o más comunidades; la densidad en las zonas de solapamiento no superó la de dentro de las comunidades.", "Poco", "No se cumplió la observación de clase y 90 de 270 proveedores quedaron sin comunidad."),
        ("Embeddings SVD y node2vec (Parte VI)", f"Entre {100 * svd.pureza_vecinos:.0f}% y {100 * n2v.pureza_vecinos.max():.0f}% de los vecinos más cercanos están en la misma comunidad de Louvain (al azar, {100 * p6['linea_base_pureza_azar']:.0f}%). p y q casi no cambian el resultado.", "Medio", "Reproducen lo que ya mostró Louvain; sirven para visualizar y comparar proveedores, no para descubrir algo nuevo."),
    ], columns=["Técnica", "Qué mostró", "Aportó", "Por qué"])
    st.dataframe(t, width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.** Aportó **mucho** lo que dio una respuesta nueva y fácil de explicar. Aportó **poco** lo que repitió algo ya sabido (HITS y el tamaño de la entidad, los embeddings y Louvain) o no mejoró la referencia (híbrido, BigCLAM).
Una técnica con poco aporte **no es un fracaso**: confirmar que dos miradas coinciden también es un resultado.
""")

with tab_conv:
    st.success("**Respuesta corta.** Los grupos que miran la **red** convergen (comunidades y embeddings). Los grupos por **características** no coinciden con los de la red. Son miradas distintas, no una contradicción.")
    st.markdown("Se compararon los grupos de **tres miradas distintas**: por características del proveedor (clustering, Parte II), por red (comunidades, Parte V) y por vector (embeddings, Parte VI). La comparación K-Means frente a Louvain usa solo los proveedores que aparecen en la muestra de 5,000 del gráfico de la Parte II y en el núcleo de la Parte VI; se cruzan por RUC (enmascarado en personas naturales), así que es una **estimación aproximada**.")
    c = pd.DataFrame([
        ("Embeddings frente a comunidades de Louvain", f"ARI {svd.ARI_vs_louvain:.2f} (SVD) y de {n2v.ARI_vs_louvain.min():.2f} a {n2v.ARI_vs_louvain.max():.2f} (node2vec)", "Sí coinciden. Los dos miran la misma red."),
        ("Embeddings frente a los tipos de proveedor (Parte II)", f"ARI {ari3['SVD']} (SVD) y {ari3['node2vec']} (node2vec)", "No coinciden. Una mirada es por conducta; la otra, por con quién se cruza."),
        ("Clústeres K-Means de la Parte II frente a comunidades de Louvain", f"ARI {ari_km_lou:.3f} en {len(cruce)} proveedores que están en ambos", "No coinciden. Los grupos por conducta cruzan todas las comunidades de la red."),
        ("BigCLAM frente a Louvain (muestra de 270)", f"ARI {bc['ari_vs_louvain']:.2f}", "En parte. Comparten la estructura general, pero BigCLAM deja a muchos sin comunidad."),
        ("PageRank frente a HITS", f"Correlación de rangos {p4['hits']['spearman_autoridad_vs_pagerank']:.2f}", "No coinciden. PageRank mira quién gana frente a quién; HITS, quién compra a quién."),
        ("Comunidades frente a rubro", f"En {n_cat} de las 10 mayores, más de 80% es del mismo rubro", "Sí coinciden. El rubro explica buena parte de las comunidades."),
    ], columns=["Comparación", "Medida", "Lectura"])
    st.dataframe(c, width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.**
- **ARI** (índice de Rand ajustado) compara dos agrupaciones: 1 = iguales; 0 = como el azar.
- **Convergen los métodos que miran la misma red** (comunidades y embeddings). Era esperable: parten del mismo grafo de co-participación.
- **No convergen con los clústeres por características** (ni los embeddings ni las comunidades), y eso **no es una contradicción**: un proveedor puede ser «activo» (característica) y estar en una comunidad de rubro (red). Cada mirada responde otra pregunta. Usarlas **juntas** da una descripción más completa.
- Las comunidades se explican sobre todo por **rubro** (bienes, servicios u obras); la región pesa menos.
""")

with tab_esc:
    st.success("**Respuesta corta.** Escalaron los métodos que recorren aristas (PageRank, Louvain). Exigieron muestra los que recalculan sobre toda la red o usan una matriz n × n. La muestra sirve para comparar métodos, no para describir el mercado.")
    t = pd.DataFrame([
        ("Grafo de co-participación (Spark)", f"{g['grafo_final']['nodos']:,} proveedores, {g['grafo_final']['aristas']:,} aristas", "Escaló", "Con tope de 30 postores por proceso: cubre 90.8% de los procesos y evita unos 20 millones de pares (sin tope serían 31.4 millones).", "Los procesos con más de 30 postores quedan fuera."),
        ("PageRank (Spark)", f"{p4['grafo_pagerank']['nodos']:,} proveedores, {p4['grafo_pagerank']['aristas']:,} aristas", "Escaló", "Ranking sobre todo el grafo de derrotas.", "Solo proveedores con 5 o más participaciones."),
        ("Louvain", f"Grafo completo: {p5['grafo']['nodos']:,} proveedores", "Escaló", f"{int(lou['comunidades'])} comunidades en {lou['segundos']:.0f} segundos.", "Hay unas 100 islas muy pequeñas que no aportan."),
        ("Girvan–Newman", f"Muestra de {p5['subgrafo']['nodos']} proveedores", "Exigió muestra", f"Se ve cómo se parte la red paso a paso (Q = {p5['gn']['mejor_Q']:.2f}).", f"Un solo cálculo en el grafo completo tardaría unas {p5['escala']['horas_estimadas_un_betweenness_grafo_completo']:.0f} horas (estimación); la muestra conserva solo una parte de las conexiones."),
        ("Espectral", f"Muestra de {p5['subgrafo']['nodos']} proveedores", "Exigió muestra", "Permite ver el número de grupos con el eigengap y con Q.", "Necesita una matriz de n × n (unos 1,600 millones de celdas con todos los proveedores)."),
        ("BigCLAM", f"Muestra de {p5['subgrafo']['nodos']} proveedores", "Exigió muestra", "Permite ver proveedores en más de una comunidad.", "Con una red tan dispersa (densidad 0.023) el resultado es poco concluyente."),
        ("Embeddings", f"Núcleo de {nucleo:,} proveedores ({100 * nucleo / p5['grafo']['nodos']:.1f}% del grafo)", "Exigió núcleo", "Vectores de buena calidad para los proveedores más activos.", "No describe a los proveedores con pocas participaciones; node2vec exige recalcular para un proveedor nuevo."),
    ], columns=["Método", "Tamaño usado", "¿Escaló?", "Qué se gana", "Qué se pierde"])
    st.dataframe(t, width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.** Los métodos que **recorren aristas** (PageRank, Louvain, LPA) escalaron. Los que **recalculan sobre toda la red** o necesitan una **matriz densa** (Girvan–Newman, espectral exacto) exigieron una muestra.
Una muestra sirve para **comparar métodos**, no para **describir el mercado**: por eso la descripción del mercado sale de Louvain sobre el grafo completo.
""")

with tab_etica:
    st.success("**Respuesta corta.** Los resultados son señales para revisar, no acusaciones. Hace falta transparencia del método, enmascarar datos personales y revisión humana antes de usar cualquier lista.")
    st.markdown("""
**Señales, no acusaciones**
- Un PageRank alto, una comunidad o un vecino cercano en el embedding **no prueban acuerdos ni irregularidades**. Reflejan tamaño, rubro, región o simple coincidencia en los procesos.
- Las comunidades se explican sobre todo por rubro: dos proveedores del mismo rubro se cruzan en los mismos procesos **de forma natural**.
- Antes de concluir algo habría que mirar **quién compra, qué compra y en qué fechas**, y conversar con quien conoce el contexto.

**Transparencia**
- El método, los parámetros y las limitaciones están escritos en cada página y en el README.
- Los resultados se pueden reproducir con los notebooks y los parámetros se pueden mover en la web: cualquiera puede ver cuánto cambian las conclusiones.

**Uso responsable**
- Se enmascaran los RUC que no empiezan con 20 y se reemplazan los nombres de personas naturales.
- Una lista ordenada puede **estigmatizar** a quien aparece arriba. Por eso se presenta como **lista para revisar**, con la explicación de por qué sube o baja cada proveedor.
- **Sesgos y vacíos:** los consorcios (21.8% de las adjudicaciones) quedan fuera del análisis; se limitó a procesos con hasta 30 postores; y los proveedores grandes pesan más en todas las medidas.
- **Qué no se debe hacer:** usar estas medidas para sancionar o excluir a un proveedor, o publicar nombres sin revisión humana.
""")

with tab_vol:
    st.success("**Respuesta corta.** Cambiaría sobre todo la escala de los métodos de comunidades y embeddings; la construcción del grafo necesitaría muestreo de aristas.")
    st.markdown("""
Estas respuestas son **hipótesis** razonadas a partir de lo medido: no se probaron con más datos.

| Si el volumen fuera mucho mayor | Qué cambiaría |
|---|---|
| **Construcción del grafo** | El número de pares crece con el cuadrado de los postores por proceso: el tope de postores pasaría de ser una comodidad a ser obligatorio, o se pasaría a aristas por muestreo. |
| **PageRank** | Ya corre en Spark; seguiría igual en un clúster real (por ejemplo con GraphFrames). Con β alto hacen falta más iteraciones. |
| **Comunidades** | LPA es el que más se adapta a un clúster; Louvain exigiría una versión distribuida. Girvan–Newman y el espectral exacto seguirían fuera: solo con aproximaciones. |
| **BigCLAM** | Habría que usar la versión por bloques del método original, en lugar de la implementación simple de NumPy. |
| **Embeddings** | SVD aleatorizada o node2vec con muestreo de vecinos, y un núcleo más grande. |
| **Si la cobertura fuera mayor** | Más años permitirían medir la **estabilidad en el tiempo** de las comunidades y del PageRank, que aquí no se pudo medir. |
""")

st.warning("Todo lo que muestra este proyecto es una **señal descriptiva para revisar**. No identifica irregularidades ni demuestra acuerdos entre proveedores.")
st.caption("Parte VII. Resume los resultados de los notebooks `P2_01` a `P2_09`.")
siguiente("pages/10_Discusion_Critica.py", "Discusión crítica del Proyecto 1")
