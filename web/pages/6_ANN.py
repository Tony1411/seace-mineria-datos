
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import cargar_json, encabezado, siguiente


st.title("Búsqueda aproximada de vecinos — ANN")

encabezado(
    '¿Se pueden buscar los textos más parecidos mucho más rápido que comparando con todos?',
    'HNSW (ef=16) recupera el 96.1% de los vecinos exactos y es unas 20 veces más rápido (0.097 ms frente a 1.91 ms). IVF fue más lento que la búsqueda exacta desde nprobe 64.',
)

st.markdown("""
### Pregunta de interés

¿Cuánto se pierde en precisión y cuánto se gana en velocidad
al utilizar búsqueda aproximada de vecinos en lugar de
búsqueda exacta?

Se comparan dos métodos:

- **IVF:** búsqueda mediante listas invertidas.
- **HNSW:** búsqueda mediante un grafo jerárquico.

**Pipeline:** textos SEACE → representación vectorial →
índice ANN → búsqueda de vecinos → evaluación de recall y tiempo.
""")


# =====================================================
# CARGA DE ARTEFACTOS
# =====================================================

datos_curvas = cargar_json("ann", "ann_curvas.json")
datos_ejemplos = cargar_json("ann", "ann_ejemplos.json")
datos_resumen = cargar_json("ann", "ann_resumen.json")

df_curvas = pd.DataFrame(datos_curvas["datos"])
df_ejemplos = pd.DataFrame(datos_ejemplos["datos"])
df_resumen = pd.json_normalize(datos_resumen["datos"])

for columna in [
    "valor",
    "recall_10",
    "ms_por_consulta",
    "veces_mas_rapido",
]:
    df_curvas[columna] = pd.to_numeric(
        df_curvas[columna],
        errors="coerce",
    )


tab_rendimiento, tab_ejemplos, tab_indices = st.tabs([
    "Precisión y velocidad",
    "Ejemplos de búsqueda",
    "Construcción de índices",
])


# =====================================================
# TAB 1: PRECISIÓN Y VELOCIDAD
# =====================================================

with tab_rendimiento:

    st.subheader("1. Configuración del método")

    metodo = st.selectbox(
        "Método ANN",
        options=["IVF", "HNSW"],
    )

    df_metodo = df_curvas[
        df_curvas["metodo"] == metodo
    ].sort_values("valor")

    valores = df_metodo["valor"].dropna().astype(int).tolist()

    valor = st.select_slider(
        "Parámetro: " + (
            "nprobe" if metodo == "IVF" else "efSearch"
        ),
        options=valores,
        value=valores[len(valores) // 2],
    )

    fila = df_metodo[
        df_metodo["valor"] == valor
    ].iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Recall@10",
        f"{fila['recall_10'] * 100:.2f}%",
    )

    c2.metric(
        "Tiempo por consulta",
        f"{fila['ms_por_consulta']:.3f} ms",
    )

    c3.metric(
        "Aceleración frente a exacta",
        f"{fila['veces_mas_rapido']:.2f}×",
    )

    st.subheader("2. Recall vs tiempo de consulta")

    fig = px.line(
        df_curvas.sort_values(["metodo", "valor"]),
        x="ms_por_consulta",
        y="recall_10",
        color="metodo",
        markers=True,
        log_x=True,
        hover_data=[
            "parametro",
            "valor",
            "veces_mas_rapido",
        ],
        labels={
            "ms_por_consulta": "Tiempo por consulta (ms)",
            "recall_10": "Recall@10",
            "metodo": "Método",
        },
        title="Compromiso entre precisión y velocidad",
    )

    fig.add_trace(
        go.Scatter(
            x=[fila["ms_por_consulta"]],
            y=[fila["recall_10"]],
            mode="markers",
            marker=dict(
                size=17,
                symbol="circle-open",
                color="black",
                line=dict(width=3),
            ),
            name="Configuración seleccionada",
        )
    )

    # Referencia de búsqueda exacta
    meta = datos_curvas.get("meta", {})
    exacta = meta.get("exacta", {})

    if isinstance(exacta, dict):
        tiempo_exacto = exacta.get("ms_por_consulta")

        if isinstance(tiempo_exacto, (int, float)):
            if tiempo_exacto > 0:
                fig.add_vline(
                    x=tiempo_exacto,
                    line_dash="dash",
                    annotation_text="Búsqueda exacta",
                )

    st.plotly_chart(
        fig,
        width="stretch",
    )

    st.caption(
        "Recall@10 mide qué proporción de los 10 vecinos "
        "exactos también se recupera con ANN."
    )

    st.subheader("3. Rendimiento según el parámetro")

    fig_param = px.line(
        df_metodo,
        x="valor",
        y="recall_10",
        markers=True,
        labels={
            "valor": "nprobe" if metodo == "IVF" else "efSearch",
            "recall_10": "Recall@10",
        },
        title=f"Efecto del parámetro en {metodo}",
    )

    st.plotly_chart(
        fig_param,
        width="stretch",
    )

    st.markdown("""
    ### Interpretación

    Una configuración más exhaustiva generalmente mejora
    la recuperación de vecinos, pero incrementa el costo
    de consulta.

    - En **IVF**, incrementar `nprobe` permite explorar
      más listas del índice.
    - En **HNSW**, incrementar `efSearch` amplía la búsqueda
      dentro del grafo.

    El objetivo es encontrar una configuración que
    mantenga un recall alto con un tiempo menor
    que la búsqueda exacta.
    """)


# =====================================================
# TAB 2: EJEMPLOS DE BÚSQUEDA
# =====================================================

with tab_ejemplos:

    st.subheader("Ejemplos de vecinos recuperados")

    st.markdown("""
    Se presentan consultas reales precalculadas,
    comparando los vecinos obtenidos mediante búsqueda
    exacta y HNSW.
    """)

    indice = st.selectbox(
        "Selecciona una consulta",
        options=list(range(len(df_ejemplos))),
        format_func=lambda i: (
            f"Consulta {i + 1}: "
            f"{str(df_ejemplos.iloc[i]['consulta'])[:85]}"
        ),
    )

    ejemplo = df_ejemplos.iloc[indice]

    st.markdown("#### Texto consultado")
    st.write(ejemplo["consulta"])

    st.metric(
        "Coincidencias en Top 5",
        f"{int(ejemplo['coinciden_en_top5'])} / 5",
    )

    vecinos_exactos = pd.DataFrame(
        ejemplo["vecinos_exactos"]
    )

    vecinos_hnsw = pd.DataFrame(
        ejemplo["vecinos_hnsw"]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Búsqueda exacta")
        st.dataframe(
            vecinos_exactos,
            width="stretch",
            hide_index=True,
        )

    with col2:
        st.markdown("#### HNSW")
        st.dataframe(
            vecinos_hnsw,
            width="stretch",
            hide_index=True,
        )

    st.markdown("""
    ### Interpretación

    El método aproximado puede recuperar vecinos
    diferentes de los identificados por la búsqueda
    exacta.

    Una coincidencia alta en el Top 5 indica que
    HNSW recupera gran parte de los vecinos relevantes
    definidos por la referencia exacta.

    Estos 20 ejemplos son ilustrativos; las métricas
    generales de rendimiento deben evaluarse en
    la pestaña anterior.
    """)


# =====================================================
# TAB 3: CONSTRUCCIÓN DE ÍNDICES
# =====================================================

with tab_indices:

    st.subheader("Comparación de índices")

    st.markdown("""
    Resultados precalculados de construcción y tamaño
    de las estructuras utilizadas para búsqueda de vecinos.
    """)

    st.dataframe(
        df_resumen,
        width="stretch",
        hide_index=True,
    )

    st.subheader("Referencia de búsqueda exacta")

    st.json(
        datos_curvas.get("meta", {}).get("exacta", {})
    )

    st.markdown("""
    ### Consideraciones

    - El tiempo de construcción y la memoria del índice
      deben considerarse junto al tiempo de consulta.
    - Los tiempos medidos dependen del hardware utilizado.
    - Los controles seleccionan experimentos precalculados;
      no se reconstruyen los índices desde la web.
    - Un recall elevado no implica necesariamente que
      todos los vecinos sean recuperados correctamente.
    """)

# Interpretación actualizada
from pathlib import Path

ruta_texto_ann = (
    Path(__file__).resolve().parents[2]
    / "web_artefactos"
    / "ann"
    / "texto_ann.md"
)

with st.expander("Metodología, hallazgos y limitaciones"):
    st.markdown(
        ruta_texto_ann.read_text(encoding="utf-8")
    )

siguiente('pages/1_Bloom_Filter.py', 'Bloom Filter')
