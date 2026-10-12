import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente


st.title("Bloom Filter")

encabezado(
    '¿Cómo saber si un postor ya había participado, usando poca memoria?',
    'Con 10 bits por elemento, el Bloom Filter tiene 0.12% de falsos positivos y ocupa 276 KiB, frente a unos 19 MiB de un conjunto exacto.',
)

st.markdown(
    """
    ### Pregunta de interés

    ¿Es posible detectar con poca memoria si un postor ya había
    participado anteriormente en algún proceso de contratación?

    El Bloom Filter permite responder consultas de pertenencia utilizando
    una estructura compacta, a cambio de aceptar falsos positivos.
    """
)


df_mem = cargar_csv(
    "bloom",
    "bloom_memoria.csv"
)

df_k = cargar_csv(
    "bloom",
    "bloom_num_hashes.csv"
)


st.subheader("Memoria vs falsos positivos")

bpe = st.select_slider(
    "Bits por elemento",
    options=sorted(
        df_mem["bits_por_elemento"].unique()
    ),
    value=10,
)

fila = df_mem[
    df_mem["bits_por_elemento"] == bpe
].iloc[0]


c1, c2, c3 = st.columns(3)

c1.metric(
    "Memoria",
    f"{fila['memoria_kib']:.2f} KiB"
)

c2.metric(
    "Funciones hash",
    int(fila["k_hashes"])
)

c3.metric(
    "FPR observado",
    f"{fila['fpr_observado_pct']:.4f}%"
)


fig = px.line(
    df_mem,
    x="memoria_kib",
    y="fpr_observado_pct",
    markers=True,
    labels={
        "memoria_kib": "Memoria (KiB)",
        "fpr_observado_pct": "FPR observado (%)",
    },
    title="Memoria vs tasa de falsos positivos",
)

st.plotly_chart(
    fig,
    width="stretch"
)


st.subheader("Efecto del número de hashes")

k = st.select_slider(
    "Número de funciones hash",
    options=sorted(
        df_k["k_hashes"].unique()
    ),
    value=7,
)

fila_k = df_k[
    df_k["k_hashes"] == k
].iloc[0]


c1, c2 = st.columns(2)

c1.metric(
    "FPR observado",
    f"{fila_k['fpr_observado_pct']:.4f}%"
)

c2.metric(
    "Tiempo",
    f"{fila_k['tiempo_s']:.2f} s"
)


fig_k = px.line(
    df_k,
    x="k_hashes",
    y="fpr_observado_pct",
    markers=True,
    labels={
        "k_hashes": "Número de hashes",
        "fpr_observado_pct": "FPR observado (%)",
    },
    title="Número de hashes vs falsos positivos",
)

st.plotly_chart(
    fig_k,
    width="stretch"
)


st.markdown(
    """
    ### Interpretación

    Aumentar la memoria reduce fuertemente la tasa de falsos positivos.

    Con aproximadamente **10 bits por elemento y 7 funciones hash**
    se obtuvo un buen compromiso entre memoria, precisión y tiempo.

    Incrementar el número de hashes más allá del valor óptimo no mejora
    necesariamente el resultado y aumenta el costo computacional.
    """
)

siguiente('pages/2_Count_Min_Sketch.py', 'Count-Min Sketch')
