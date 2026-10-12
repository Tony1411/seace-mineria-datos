
import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("Count-Min Sketch")

encabezado(
    '¿Cuántas veces participa cada postor, sin guardar un contador por postor?',
    'Con ancho 50,000, el error absoluto medio es 3.87 (la media real es 11.02). Con ancho 2,719 sube a 416. El top 10 de postores suma solo el 2.7% de las participaciones.',
)

st.markdown("""
### Pregunta de interés

¿Con qué precisión podemos estimar la frecuencia de participación
de los postores utilizando una estructura de memoria acotada?

**Pipeline:** participaciones SEACE → RUC → Count-Min Sketch
→ estimación → comparación con frecuencias exactas.

Se procesaron 2,493,612 participaciones correspondientes a
226,293 RUC distintos.
""")

df_width = cargar_csv("cms", "cms_width.csv")
df_depth = cargar_csv("cms", "cms_depth.csv")

# Experimento 1: width
st.subheader("1. Efecto del ancho (width)")

st.caption("Profundidad fija: depth = 5")

width = st.select_slider(
    "Selecciona width",
    options=sorted(df_width["width"].unique()),
    value=50000,
)

fila = df_width[df_width["width"] == width].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("MAE", f"{fila['mae']:.2f}")
c2.metric("Memoria", f"{fila['memoria_kib']:.2f} KiB")
c3.metric("Error máximo", f"{fila['max_error']:.0f}")

fig = px.line(
    df_width,
    x="memoria_kib",
    y="mae",
    markers=True,
    title="Memoria vs error absoluto medio",
    labels={
        "memoria_kib": "Memoria (KiB)",
        "mae": "MAE",
    },
)
st.plotly_chart(fig, width="stretch")

# Experimento 2: depth
st.subheader("2. Efecto de la profundidad (depth)")

st.caption("Ancho fijo: width = 20,000")

depth = st.select_slider(
    "Selecciona depth",
    options=sorted(df_depth["depth"].unique()),
    value=5,
)

fila_d = df_depth[df_depth["depth"] == depth].iloc[0]

c1, c2, c3 = st.columns(3)
c1.metric("MAE", f"{fila_d['mae']:.2f}")
c2.metric("Memoria", f"{fila_d['memoria_kib']:.2f} KiB")
c3.metric("P95 del error", f"{fila_d['p95_error']:.0f}")

fig_d = px.line(
    df_depth,
    x="depth",
    y="mae",
    markers=True,
    title="Profundidad vs error absoluto medio",
    labels={
        "depth": "Número de filas",
        "mae": "MAE",
    },
)
st.plotly_chart(fig_d, width="stretch")

st.markdown("""
### Interpretación

Aumentar `width` reduce considerablemente las colisiones
y, por tanto, el error de estimación.

Aumentar `depth` también mejora la precisión, pero presenta
rendimientos decrecientes y requiere más memoria.

La configuración `width=50000`, `depth=5` ofrece un
compromiso razonable, con MAE cercano a 3.87 y memoria
aproximada de 977 KiB.

**Nota metodológica:** los controles muestran experimentos
precalculados. El barrido de width mantiene depth=5, mientras
que el barrido de depth mantiene width=20000.
Los tiempos de estos barridos corresponden a actualizaciones
agrupadas por RUC, no a reproducir el flujo cronológico completo.
""")

siguiente('pages/3_DGIM.py', 'DGIM')
