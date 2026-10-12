
import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("DGIM")

encabezado(
    '¿Cuántos de los últimos procesos fueron desiertos, sin guardar toda la ventana?',
    'DGIM estima con un error relativo de 9% a 12% y unos 66 bytes teóricos para una ventana de 50,000 procesos.',
)

st.markdown("""
### Pregunta de interés

¿Cuántos de los últimos W procesos de contratación
fueron declarados desiertos?

**Pipeline:** procesos SEACE → orden cronológico →
codificación binaria → DGIM → estimación vs conteo exacto.

Se analizaron 209,740 procesos, de los cuales
25,268 estaban clasificados como DESIERTO.
""")

df = cargar_csv("dgim", "dgim_ventanas.csv")

# Selector de ventana
st.subheader("1. Configuración de ventana")

window = st.select_slider(
    "Tamaño de ventana (últimos W procesos)",
    options=sorted(df["window_size"].unique()),
    value=5000,
)

fila = df[df["window_size"] == window].iloc[0]

c1, c2, c3 = st.columns(3)

c1.metric(
    "Conteo exacto final",
    f"{fila['exacto_final']:.0f}"
)

c2.metric(
    "Estimación DGIM final",
    f"{fila['estimado_final']:.1f}"
)

c3.metric(
    "Error absoluto final",
    f"{fila['error_final']:.1f}"
)

c4, c5, c6 = st.columns(3)

c4.metric(
    "Error relativo medio",
    f"{fila['error_rel_pct']:.2f}%"
)

c5.metric(
    "Máximo de buckets",
    int(fila["max_buckets"])
)

c6.metric(
    "Memoria teórica aprox.",
    f"{fila['memoria_teorica_bytes']:.1f} B"
)

# Comparación exacto vs estimado
st.subheader("2. Comparación de resultados")

df_comparacion = df.melt(
    id_vars="window_size",
    value_vars=["exacto_final", "estimado_final"],
    var_name="metodo",
    value_name="conteo",
)

fig = px.line(
    df_comparacion,
    x="window_size",
    y="conteo",
    color="metodo",
    markers=True,
    title="Conteo exacto vs estimación DGIM al final del flujo",
    labels={
        "window_size": "Tamaño de ventana",
        "conteo": "Número de procesos desiertos",
        "metodo": "Método",
    },
    log_x=True,
)

st.plotly_chart(fig, width="stretch")

# Error relativo
st.subheader("3. Error relativo medio")

fig_error = px.line(
    df,
    x="window_size",
    y="error_rel_pct",
    markers=True,
    log_x=True,
    title="Error relativo medio por tamaño de ventana",
    labels={
        "window_size": "Tamaño de ventana",
        "error_rel_pct": "Error relativo medio (%)",
    },
)

st.plotly_chart(fig_error, width="stretch")

st.markdown("""
### Interpretación

DGIM permite estimar el número de procesos desiertos
en ventanas recientes sin almacenar todo el historial.

En los experimentos realizados, el error relativo medio
se mantuvo aproximadamente entre 9% y 12%.

El número máximo de buckets aumentó lentamente con
el tamaño de la ventana, mostrando el ahorro de memoria
característico del algoritmo.

**Limitaciones:**
- Las ventanas representan cantidades de procesos, no días.
- La memoria mostrada es una estimación teórica de la
  representación compacta, no el consumo real de objetos Python.
- El error relativo medio excluye consultas cuyo conteo
  exacto es cero.
- Los valores de cada ventana fueron precalculados.
""")

siguiente('pages/8_Apriori_FPGrowth.py', 'Apriori y FP-Growth')
