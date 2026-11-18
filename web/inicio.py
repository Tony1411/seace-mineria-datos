import streamlit as st

from preguntas import PREGUNTAS
from utils_p2 import csv_p2, json_p2

st.title("Minería de datos masivos sobre contrataciones públicas del Perú")
st.caption(
    "Proyecto Integrador · Minería de Datos Masivos y Flujos de Datos · Prof. Heider Sanchez · "
    "Anthony Roca · Willian Berrocal · Jimena Mamani"
)

# ---------------------------------------------------------------
# EL PROBLEMA
# ---------------------------------------------------------------
st.header("Qué queremos resolver")
st.markdown(
    """
    En 32 meses, el Estado peruano publicó **209,740 procesos de contratación** en el SEACE.
    Son demasiados para revisarlos a mano. Queremos saber qué se puede encontrar en ellos
    con técnicas que escalan (Spark, similitud, flujos y reglas de asociación),
    y **cuánta precisión se pierde al usar métodos aproximados**.
    """
)

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Procesos analizados", "209,740")
c2.metric("Entidades contratantes", "2,992")
c3.metric("Participaciones de postores", "2,493,612")
c4.metric("Textos distintos", "163,208")
c5.metric("Periodo", "2024–2026")

st.caption("Periodo analizado: enero de 2024 a agosto de 2026 (32 meses).")

st.markdown(
    "**Fuente:** Registro OCDS Perú (OECE, vía Open Contracting Partnership), "
    "licencia CC BY 4.0, con datos filtrados y limpiados por el equipo. "
    "Datos obtenidos por última vez el 4 de septiembre de 2026."
)
st.page_link("pages/0_Datos_y_Limpieza.py", label="Empezar: datos y limpieza →")

# ---------------------------------------------------------------
# LAS CINCO PREGUNTAS (EN EL ORDEN DEL RECORRIDO)
# ---------------------------------------------------------------
st.header("Cinco preguntas, en el orden del recorrido")

for p in PREGUNTAS:
    with st.container(border=True):
        st.subheader(p["titulo"])
        st.markdown(f"**Por qué importa:** {p['relevancia']}")
        st.markdown(f"**Lo que encontramos:** {p['hallazgo']}")
        columnas = st.columns(len(p["links"]))
        for col, (ruta, etiqueta) in zip(columnas, p["links"]):
            col.page_link(ruta, label=etiqueta)

# ---------------------------------------------------------------
# CONCLUSIÓN
# ---------------------------------------------------------------
st.header("Qué concluimos")
st.success(
    "- Los procesos cambian de régimen con la Ley 32069: no se pueden comparar los años como si fueran iguales.\n"
    "- Los textos repetidos están sobre todo **dentro de la misma entidad**, y LSH y HNSW los encuentran con muy poco costo.\n"
    "- Cuando no hay postores, es mucho más probable que el proceso quede desierto o nulo.\n"
    "- Aproximar vale la pena cuando el volumen lo exige. A esta escala, solo LSH era imprescindible."
)
st.warning(
    "Un texto parecido o una regla fuerte **no prueban una irregularidad**. "
    "Estas técnicas sirven para elegir casos que una persona revise. "
    "Los ejemplos con nombres de entidades muestran un patrón, no una sospecha."
)

# ---------------------------------------------------------------
# PROYECTO 2: GRAFOS, CLUSTERING Y REPRESENTACIÓN
# ---------------------------------------------------------------
st.header("Proyecto 2: quién importa, qué grupos forman y cómo se representan")
st.markdown(
    "Con las adjudicaciones y los postores se construyó una base entidad–proveedor y un grafo de co-participación "
    "(Partes I a III: clustering y recomendación). Las Partes IV a VI preguntan **quién importa en la red, qué grupos forma y cómo representar a cada proveedor**."
)
try:
    p4, p5, p6 = json_p2("p4_resumen.json"), json_p2("p5_resumen.json"), json_p2("p6_resumen.json")
    met6 = csv_p2("emb_metricas.csv")
    lou = p5["louvain_completo_resolucion_1"]
    cards = [
        ("Parte IV · PageRank y HITS",
         f"El 1% de proveedores con más PageRank ({p4['pagerank']['n_top1pct']}) reúne {100 * p4['pagerank']['masa_top1pct']:.1f}% del total. "
         "El ranking de arriba casi no cambia entre β = 0.50 y 0.95.",
         "pages/17_PageRank_HITS.py", "PageRank y HITS"),
        ("Parte V · Comunidades",
         f"Louvain encuentra {int(lou['comunidades'])} comunidades en {p5['grafo']['nodos']:,} proveedores (Q = {lou['Q']:.2f}). "
         "Girvan–Newman y el espectral solo corren sobre una muestra.",
         "pages/18_Comunidades.py", "Comunidades"),
        ("Parte VI · Embeddings",
         f"Con SVD y con node2vec, entre {100 * met6.pureza_vecinos.min():.0f}% y {100 * met6.pureza_vecinos.max():.0f}% de los vecinos más cercanos de un proveedor está en su misma comunidad "
         f"({100 * p6['linea_base_pureza_azar']:.0f}% al azar). Ninguno de los dos gana con claridad.",
         "pages/19_Embeddings.py", "Embeddings de nodos"),
    ]
    for titulo, texto, ruta, etiqueta in cards:
        with st.container(border=True):
            st.subheader(titulo)
            st.markdown(texto)
            st.page_link(ruta, label=etiqueta)
except FileNotFoundError:
    st.info("Los resultados de las Partes IV a VI se generan con los notebooks P2_07 a P2_09.")
st.caption("Todo lo de este proyecto es una señal descriptiva para revisar, no una acusación.")
