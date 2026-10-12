import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("Spark — RDD, DataFrame y particionamiento")

encabezado(
    '¿Importa cómo se agrupa y se reparte el trabajo en Spark?',
    'Sí. DataFrame fue 2.8 y 2.2 veces más rápido que RDD en dos agregaciones. repartition(200) tardó 4.13 s y repartition(4, dep) 0.30 s. Todo corrió en local[*], no en un clúster.',
)
st.markdown(
    """**Pregunta:** ¿Cómo afecta la API y la estrategia de particionamiento
    al tiempo de agregación en los datos SEACE?

    Se muestran mediciones de la ejecución local (Spark en modo local).
    No se ejecutan consultas Spark en la página.
    """
)

comparacion = cargar_csv("c", "comparacion_rdd_dataframe_resumen.csv")
particiones = cargar_csv("c", "tarea4_particiones.csv")

st.subheader("RDD frente a DataFrame")
metrica = st.radio("Estadístico", ["t_min_s", "t_mediana_s"], horizontal=True,
                  format_func=lambda v: "Tiempo mínimo" if v == "t_min_s" else "Mediana")
fig = px.bar(
    comparacion, x="agregacion", y=metrica, color="tecnica", barmode="group",
    labels={"agregacion": "Agregación", metrica: "Tiempo (s)", "tecnica": "API"},
)
st.plotly_chart(fig, width="stretch")
st.dataframe(comparacion, width="stretch", hide_index=True)
st.caption(
    "Mínimos y medianas de tres repeticiones por agregación, transcritos "
    "de las salidas del notebook de C con resolución de dos decimales."
)

st.subheader("Efecto del número y criterio de particiones")
fig2 = px.line(
    particiones, x="n_part", y="t_min_s", color="estrategia", markers=True,
    labels={"n_part": "Particiones solicitadas", "t_min_s": "Tiempo mínimo (s)",
            "estrategia": "Estrategia"},
)
st.plotly_chart(fig2, width="stretch")
st.dataframe(particiones, width="stretch", hide_index=True)

st.markdown(
    """### Interpretación y limitaciones
    En la ejecución guardada, DataFrame fue más rápido que RDD en las dos
    agregaciones. En particionamiento se observó un mínimo de ~0.303 s al
    reparticionar en cuatro particiones por departamento, comparado con ~4.128 s
    al repartir en 200 particiones sin clave.

    - Las pruebas se ejecutaron en **Spark local**, sobre datos cacheados;
      no acreditan rendimiento distribuido en varios nodos.
    - Particionar por departamento puede crear **desequilibrio** entre particiones.
    - La agregación RDD tiene una posible diferencia de denominador para
      montos de valor cero, según la revisión del notebook.
    - Los tiempos dependen de la máquina y del entorno de ejecución.
    """
)

siguiente('pages/4_Minhash_LSH.py', 'MinHash y LSH')
