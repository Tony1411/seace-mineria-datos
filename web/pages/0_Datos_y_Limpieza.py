import pandas as pd
import plotly.express as px
import streamlit as st

from utils import cargar_json, encabezado, siguiente


st.title("Datos, KDD y limpieza")

encabezado(
    "¿Qué datos usamos y qué tan confiables son?",
    "357,729 filas leídas quedaron en 209,740 procesos entre 2024-01 y 2026-08. "
    "Los datos tienen límites: no incluyen las compras sin procedimiento de selección "
    "y los estados son a la fecha de corte (3 de septiembre de 2026).",
)

reporte = cargar_json("datos", "reporte_calidad.json")
datos = reporte["datos"]

tabs = st.tabs(["Fuente", "KDD y limpieza", "Calidad y límites"])

# ---------------------------------------------------------------
# 1. FUENTE
# ---------------------------------------------------------------
with tabs[0]:
    st.markdown(
        """
        - **Dataset:** Registro OCDS Perú, publicado por el OECE (antes OSCE) y distribuido por
          Open Contracting Partnership: <https://data.open-contracting.org/es/publication/135>
        - **Licencia:** CC BY 4.0. Los datos fueron **filtrados, limpiados y transformados** por el equipo.
        - **Fecha:** obtenidos por última vez el 4 de septiembre de 2026 (última actualización: 3 de septiembre).
        """
    )
    st.markdown("**Por qué sirve para las seis técnicas:**")
    st.markdown(
        """
        - **Volumen:** 209,740 procesos y 2,493,612 participaciones de postores (CSV originales de unos 2.7 GB).
        - **Texto:** 163,208 descripciones distintas para similitud y vecinos aproximados.
        - **Tiempo:** `fecha_pub` con hora y minuto, para simular un flujo.
        - **Transacciones:** cada proceso es una canasta de características. Quedan 196,158.
        """
    )
    st.code(
        "OECE (antes OSCE), vía Open Contracting Partnership. Registro OCDS Perú. "
        "https://data.open-contracting.org/es/publication/135. CC BY 4.0. "
        "Datos filtrados, limpiados y transformados por el equipo.",
        language=None,
    )

# ---------------------------------------------------------------
# 2. KDD Y LIMPIEZA
# ---------------------------------------------------------------
with tabs[1]:
    etapas = [
        ("1. Selección", "Registro OCDS, procesos de 2024-01 a 2026-08"),
        ("2. Preprocesamiento", "Esquema explícito, fechas de Lima, deduplicar, filtrar el periodo"),
        ("3. Transformación", "Texto normalizado, estados, montos en soles, canastas"),
        ("4. Minería", "Similitud, vecinos, flujos, reglas y Spark"),
        ("5. Interpretación", "Límites y discusión crítica (Parte VI)"),
    ]
    for col, (nombre, texto) in zip(st.columns(5), etapas):
        with col.container(border=True):
            st.markdown(f"**{nombre}**")
            st.caption(texto)

    embudo = pd.DataFrame(datos["embudo"])
    fig = px.funnel(embudo, x="filas", y="etapa")
    fig.update_layout(yaxis_title=None, xaxis_title="Filas")
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        "No hubo `ocid` duplicados. **147,341 filas (41.2%)** son anteriores a 2024 y se descartaron. "
        "Se excluyeron 648 filas de septiembre de 2026 (mes parcial)."
    )

    st.markdown("**Decisiones más importantes**")
    st.table(pd.DataFrame([
        {"Decisión": "Periodo desde 2024-01, sin septiembre 2026",
         "Por qué": "Volumen suficiente y datos recientes. Septiembre tiene solo 3 días y distorsionaría los conteos."},
        {"Decisión": "Monto 0 = no disponible",
         "Por qué": "Ningún proceso cuesta 0. El 78% de esos ceros es información protegida por ley."},
        {"Decisión": "Usar `procedimiento` y no `metodo`",
         "Por qué": "`metodo` está vacío en cerca del 30%, casi todos procedimientos nuevos (desde abril 2025)."},
        {"Decisión": "No corregir la caída de mayo 2025",
         "Por qué": "Coincide con la Ley 32069. Es un cambio real, no un error de datos."},
        {"Decisión": "Estado del proceso = estado único de sus ítems, o `MIXTO`",
         "Por qué": "Un proceso puede tener ítems con estados distintos. `MIXTO` es el 3.2%."},
        {"Decisión": "No usar el Padrón RUC de SUNAT",
         "Por qué": "El dataset OCDS cumple los requisitos del proyecto por sí solo."},
    ]))
    st.caption("Las 14 decisiones completas están en el notebook `B_00_Limpieza`.")

# ---------------------------------------------------------------
# 3. CALIDAD Y LÍMITES
# ---------------------------------------------------------------
with tabs[2]:
    nulos = pd.DataFrame(datos["nulos"])
    fig = px.bar(nulos, x="pct_nulo", y="columna", orientation="h",
                 labels={"pct_nulo": "% de nulos", "columna": ""},
                 title="Columnas con más nulos en `procesos`")
    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "`proyecto_id` (60% nulo) no se usa. `valor_pen_valido` es nulo por los montos 0, "
        "y `monto_adj_pen` por los procesos sin adjudicación."
    )

    st.markdown("**Qué hay que tener presente**")
    st.markdown(
        """
        - **No están todas las compras públicas.** Faltan las que no pasan por un procedimiento de selección.
        - **Los estados son a la fecha de corte.** Los procesos recientes están más abiertos:
          `CONVOCADO` es 13.5% en 2026 y 4.7% en 2024.
        - **Cambio de ley en abril de 2025.** Antes y después no son el mismo régimen.
        - **Montos 0 y protegidos no son montos reales.**
        - **Departamento y tipo de entidad son aproximados:** el departamento es la sede de la entidad
          (no el lugar de ejecución) y el tipo se deduce del nombre (el 23% queda como `otro`).
        """
    )

siguiente("pages/0_EDA.py", "Análisis exploratorio")
