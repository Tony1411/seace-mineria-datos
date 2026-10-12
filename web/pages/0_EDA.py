
import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("Análisis exploratorio — SEACE")

encabezado(
    '¿Cómo se mueven los procesos en el tiempo y qué cambió con la Ley 32069?',
    'Abril de 2025 tiene el máximo de la serie (9,356 procesos) y mayo cae a 3,646. Coincide con la ley (22 de abril de 2025), pero no prueba causa.',
)

st.markdown("""
**Periodo:** enero de 2024 a agosto de 2026.

Se analizaron 209,740 procesos de contratación pública mediante
Apache Spark. Los gráficos utilizan agregados precalculados.
""")

tabs = st.tabs([
    "Temporal",
    "Categorías",
    "Procedimientos",
    "Territorio",
    "Montos",
    "Estados",
])

# 1. EVOLUCIÓN TEMPORAL
with tabs[0]:
    st.subheader("Evolución de procesos por mes")

    df = cargar_csv("eda", "procesos_por_mes.csv")

    fig = px.line(
        df,
        x="periodo",
        y="n_procesos",
        markers=True,
        labels={
            "periodo": "Periodo",
            "n_procesos": "Número de procesos",
        },
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** enero presenta sistemáticamente una
    menor cantidad de procesos. Destaca abril de 2025 con
    9,356 procesos, seguido por una fuerte caída en mayo
    a 3,646. Este cambio coincide temporalmente con la
    entrada en vigencia de la Ley 32069, aunque no
    demuestra por sí solo una relación causal.
    """)

# 2. CATEGORÍAS
with tabs[1]:
    st.subheader("Categorías de contratación")

    df = cargar_csv("eda", "procesos_por_categoria.csv")

    fig = px.bar(
        df,
        x="categoria",
        y="n_procesos",
        text="porcentaje",
        labels={
            "categoria": "Categoría",
            "n_procesos": "Número de procesos",
        },
    )
    fig.update_traces(texttemplate="%{text:.2f}%")
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** bienes (43.49%) y servicios (43.85%)
    presentan participaciones similares, mientras que
    obras representa el 12.65% de los procesos.
    """)

# 3. PROCEDIMIENTOS
with tabs[2]:
    st.subheader("Procedimientos más frecuentes")

    df = cargar_csv(
        "eda", "top_procedimientos_por_anio.csv"
    )

    anios = sorted(df["anio_pub"].unique())

    anio = st.selectbox(
        "Selecciona el año",
        options=anios,
        index=len(anios) - 1,
    )

    filtrado = (
        df[df["anio_pub"] == anio]
        .sort_values("n_procesos")
    )

    fig = px.bar(
        filtrado,
        x="n_procesos",
        y="procedimiento",
        orientation="h",
        labels={
            "n_procesos": "Número de procesos",
            "procedimiento": "Procedimiento",
        },
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** la Adjudicación Simplificada
    dominaba en 2024. Desde 2025 ganaron protagonismo
    la Licitación Pública Abreviada y el Concurso Público
    Abreviado, en un contexto de cambio normativo.

    Los datos de 2026 abarcan únicamente enero-agosto.
    """)

# 4. TERRITORIO
with tabs[3]:
    st.subheader("Distribución por departamento")

    df = cargar_csv(
        "eda", "procesos_por_departamento.csv"
    )

    df = df.copy()
    df["procesos_por_entidad"] = (
        df["n_procesos"] / df["n_entidades"]
    )

    metrica = st.radio(
        "Métrica territorial",
        options=[
            "Número de procesos",
            "Procesos por entidad",
        ],
        horizontal=True,
    )

    columna = (
        "n_procesos"
        if metrica == "Número de procesos"
        else "procesos_por_entidad"
    )

    filtrado = df.sort_values(columna)

    fig = px.bar(
        filtrado,
        x=columna,
        y="entidad_departamento",
        orientation="h",
        height=750,
        labels={
            columna: metrica,
            "entidad_departamento": "Departamento",
        },
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** Lima concentra el 29.94%
    de los procesos. Sin embargo, Callao presenta
    el mayor promedio de procesos por entidad (139.11).

    La ubicación corresponde a la sede administrativa
    de la entidad contratante, no al lugar de ejecución.
    """)

# 5. MONTOS
with tabs[4]:
    st.subheader("Valores referenciales")

    df = cargar_csv("eda", "montos_por_categoria.csv")

    metrica = st.selectbox(
        "Estadística",
        options=["mediana", "p90", "media"],
    )

    fig = px.bar(
        df,
        x="categoria",
        y=metrica,
        labels={
            "categoria": "Categoría",
            metrica: "Monto referencial (S/)",
        },
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** la distribución es fuertemente
    asimétrica. La mediana global es aproximadamente
    S/ 195,526, frente a una media de S/ 1.67 millones.

    Las obras presentan montos típicos superiores.
    La cobertura de montos válidos es 89.65%.
    """)

# 6. ESTADOS
with tabs[5]:
    st.subheader("Estado de los procesos")

    df = cargar_csv("eda", "estados_procesos.csv")
    df = df.sort_values(
        "n_procesos", ascending=False
    ).head(10)

    fig = px.bar(
        df.sort_values("n_procesos"),
        x="n_procesos",
        y="estado_proceso",
        orientation="h",
        labels={
            "n_procesos": "Número de procesos",
            "estado_proceso": "Estado",
        },
    )
    st.plotly_chart(fig, width="stretch")

    st.markdown("""
    **Interpretación:** el 62.53% de los procesos está
    clasificado como CONTRATADO y el 12.05% como DESIERTO.

    Los estados corresponden a la fecha de corte del
    dataset. Los procesos recientes pueden permanecer
    abiertos, por lo que no deben considerarse
    automáticamente fallidos.
    """)

siguiente('pages/9_Spark_Particiones.py', 'Spark y particiones')
