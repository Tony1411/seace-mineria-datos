import streamlit as st

from preguntas import PREGUNTAS

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
