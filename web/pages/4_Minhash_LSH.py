
import math

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import cargar_json, encabezado, siguiente


st.title("Detección de textos similares — MinHash y LSH")

encabezado(
    '¿Cómo encontrar textos casi iguales sin comparar todos los pares?',
    'MinHash estima la similitud con error medio de 0.027 (128 hashes). LSH revisa 693,144 candidatos, el 0.005% de los 13,318,344,028 pares posibles. De esos candidatos, el 10.3% son pares reales con similitud de 0.7 o más: hay que verificarlos.',
)

st.markdown("""
Análisis de similitud entre las descripciones de los
procesos de contratación pública del SEACE.

Se utilizan resultados precalculados.
""")

tab_minhash, tab_lsh = st.tabs(["MinHash", "LSH"])


# =====================================================
# MINHASH
# =====================================================

with tab_minhash:
    st.subheader("Estimación de similitud con MinHash")

    st.markdown("""
    **Pregunta:** ¿Cómo cambia el error al estimar
    la similitud de Jaccard cuando aumentamos
    el número de funciones hash?
    """)

    datos_error = cargar_json(
        "similitud", "minhash_error.json"
    )
    datos_pares = cargar_json(
        "similitud", "minhash_pares.json"
    )

    df_error = pd.DataFrame(
        datos_error["datos"]["global"]
    )
    df_pares = pd.DataFrame(
        datos_pares["datos"]
    )

    k = st.select_slider(
        "Número de funciones hash (k)",
        options=sorted(df_error["k"].unique().tolist()),
        value=64,
    )

    fila = df_error[df_error["k"] == k].iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Error medio absoluto",
        f"{fila['error_medio']:.4f}"
    )
    c2.metric(
        "RMSE",
        f"{fila['rmse']:.4f}"
    )
    c3.metric(
        "Percentil 95 del error",
        f"{fila['error_p95']:.4f}"
    )

    st.subheader("1. Error según número de hashes")

    fig = px.line(
        df_error,
        x="k",
        y="error_medio",
        markers=True,
        labels={
            "k": "Número de hashes",
            "error_medio": "Error medio absoluto",
        },
        title="Precisión de MinHash según k",
    )

    st.plotly_chart(fig, width="stretch")

    st.subheader("2. Jaccard exacto vs estimado")

    columna_estimacion = f"est_k{k}"

    fig_scatter = px.scatter(
        df_pares,
        x="jaccard_exacto",
        y=columna_estimacion,
        opacity=0.4,
        labels={
            "jaccard_exacto": "Jaccard exacto",
            columna_estimacion: "Jaccard estimado",
        },
        title=f"Estimaciones con k={k}",
        range_x=[0, 1],
        range_y=[0, 1],
    )

    fig_scatter.add_trace(
        go.Scatter(
            x=[0, 1],
            y=[0, 1],
            mode="lines",
            name="Estimación perfecta",
            line=dict(dash="dash"),
        )
    )

    st.plotly_chart(
        fig_scatter,
        width="stretch",
    )

    st.markdown("""
    **Interpretación:** aumentar el número de hashes
    reduce generalmente el error de estimación.
    Los puntos más próximos a la diagonal representan
    estimaciones más precisas.
    """)


# =====================================================
# LSH
# =====================================================

with tab_lsh:
    st.subheader("Locality-Sensitive Hashing")

    st.markdown("""
    **Pregunta:** ¿Cómo afectan las bandas y filas
    a la cantidad de candidatos, falsos positivos
    y falsos negativos al buscar textos similares?
    """)

    datos_lsh = cargar_json(
        "similitud", "lsh_grid.json"
    )

    df_lsh = pd.DataFrame(
        datos_lsh["datos"]
    )

    combinaciones = sorted(
        set(
            zip(
                df_lsh["bandas"].astype(int),
                df_lsh["filas"].astype(int),
            )
        ),
        reverse=True,
    )

    b, r = st.selectbox(
        "Configuración (bandas, filas)",
        options=combinaciones,
        format_func=lambda x: (
            f"{x[0]} bandas × {x[1]} filas"
        ),
    )

    umbral = st.select_slider(
        "Umbral de similitud Jaccard",
        options=sorted(
            df_lsh["umbral"].unique().tolist()
        ),
        value=0.8,
    )

    seleccionado = df_lsh[
        (df_lsh["bandas"] == b)
        & (df_lsh["filas"] == r)
        & (df_lsh["umbral"] == umbral)
    ].iloc[0]

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Precisión",
        f"{seleccionado['precision'] * 100:.2f}%"
    )
    c2.metric(
        "Recall",
        f"{seleccionado['recall'] * 100:.2f}%"
    )
    c3.metric(
        "Pares candidatos",
        f"{int(seleccionado['candidatos']):,}"
    )

    c4, c5, c6 = st.columns(3)

    c4.metric("TP", int(seleccionado["tp"]))
    c5.metric("FP", int(seleccionado["fp"]))
    c6.metric("FN", int(seleccionado["fn"]))

    st.subheader("1. Probabilidad de ser candidato")

    valores_s = [
        i / 100
        for i in range(101)
    ]

    probabilidades = [
        1 - (1 - s**r)**b
        for s in valores_s
    ]

    fig_lsh = go.Figure()

    fig_lsh.add_trace(
        go.Scatter(
            x=valores_s,
            y=probabilidades,
            mode="lines",
            name="Probabilidad de candidato",
        )
    )

    fig_lsh.add_vline(
        x=umbral,
        line_dash="dash",
        annotation_text="Umbral seleccionado",
    )

    fig_lsh.update_layout(
        title=f"Curva en S: b={b}, r={r}",
        xaxis_title="Similitud Jaccard",
        yaxis_title="Probabilidad de ser candidato",
        yaxis_range=[0, 1],
    )

    st.plotly_chart(
        fig_lsh,
        width="stretch",
    )

    umbral_efectivo = (1 / b) ** (1 / r)

    st.metric(
        "Umbral efectivo aproximado de LSH",
        f"{umbral_efectivo:.3f}",
    )

    st.subheader("2. Precisión y recall por configuración")

    df_umbral = df_lsh[
        df_lsh["umbral"] == umbral
    ].copy()

    df_umbral["configuracion"] = (
        df_umbral["bandas"].astype(str)
        + " × "
        + df_umbral["filas"].astype(str)
    )

    comparacion = df_umbral.melt(
        id_vars="configuracion",
        value_vars=["precision", "recall"],
        var_name="metrica",
        value_name="valor",
    )

    fig_comp = px.bar(
        comparacion,
        x="configuracion",
        y="valor",
        color="metrica",
        barmode="group",
        labels={
            "configuracion": "Bandas × filas",
            "valor": "Proporción",
            "metrica": "Métrica",
        },
        title=f"Comparación con umbral={umbral}",
    )

    st.plotly_chart(
        fig_comp,
        width="stretch",
    )

    st.markdown("""
    **Interpretación:** configurar más bandas favorece
    la recuperación de candidatos, mientras que exigir
    más coincidencias por banda hace el filtrado más
    selectivo.

    La curva en S describe la probabilidad teórica
    de obtener un candidato. Los valores de precisión,
    recall, TP, FP y FN corresponden a los experimentos
    reales precalculados.

    **Limitación:** los controles seleccionan únicamente
    combinaciones evaluadas previamente.
    """)

siguiente('pages/5_Casos_de_Textos.py', 'Casos de textos')
