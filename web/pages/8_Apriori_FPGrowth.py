import pandas as pd
import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("Conjuntos frecuentes — Apriori y FP-Growth")

encabezado(
    '¿Qué características aparecen juntas en un mismo proceso?',
    'FP-Growth halló 5,002 conjuntos frecuentes en los 196,158 procesos (soporte 1%, 15.6 s). La comparación de igualdad con Apriori dio False; la causa probable es el límite de 5 ítems de Apriori (hipótesis sin comprobar).',
)
st.markdown(
    """**Pregunta:** ¿Cómo varían los conjuntos frecuentes y el tiempo de ejecución
    según el algoritmo y el umbral mínimo de soporte?

    **Pipeline:** 196,158 transacciones → muestra para Apriori / Spark MLlib
    para FP-Growth → itemsets y estadísticas precalculadas.
    """
)

comparacion = cargar_csv("c", "comparacion_apriori_fpgrowth.csv")
curva = cargar_csv("c", "curva_fpgrowth.csv").sort_values("min_sup")
items = cargar_csv("c", "items_frecuencia.csv")
itemsets = cargar_csv("c", "itemsets_frecuentes.csv")

p1, p2, p3 = st.tabs(["Comparación de algoritmos", "Sensibilidad a soporte", "Explorar ítems"])

with p1:
    st.subheader("Resultados de las tres ejecuciones")
    st.dataframe(comparacion.round(3), width="stretch", hide_index=True)
    fig = px.bar(
        comparacion, x="algoritmo", y="t_s", text="n_itemsets",
        labels={"algoritmo": "Ejecución", "t_s": "Tiempo (s)", "n_itemsets": "Itemsets"},
        title="Tiempo por ejecución (etiqueta: número de itemsets)",
    )
    st.plotly_chart(fig, width="stretch")
    st.warning(
        "Apriori usa 30,188 transacciones, soporte 2% y un límite de 5 ítems. "
        "FP-Growth sobre la misma muestra no tiene ese límite (1,969 vs 2,005 itemsets). "
        "Sí se comparó la igualdad de resultados y dio False. La causa probable es "
        "ese límite de tamaño (es una hipótesis, aún sin comprobar). "
        "El FP-Growth completo usa 196,158 transacciones y soporte 1%. "
        "Los tiempos no permiten concluir cuál algoritmo es universalmente más rápido."
    )

with p2:
    soporte = st.select_slider(
        "Soporte mínimo de FP-Growth",
        options=sorted(curva["min_sup"].unique().tolist()), value=0.01,
        format_func=lambda x: f"{x * 100:g}%",
    )
    fila = curva.loc[curva["min_sup"].eq(soporte)].iloc[0]
    c1, c2 = st.columns(2)
    c1.metric("Itemsets frecuentes", f"{int(fila['n_itemsets']):,}")
    c2.metric("Tiempo", f"{fila['t_s']:.2f} s")
    fig = px.line(
        curva, x="min_sup", y="n_itemsets", markers=True,
        labels={"min_sup": "Soporte mínimo", "n_itemsets": "Número de itemsets"},
        title="Umbral mínimo de soporte y número de itemsets",
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "La curva contiene únicamente conteos y tiempos precalculados. "
        "El catálogo de 5,002 itemsets y las reglas disponibles se generaron "
        "con soporte mínimo 1%; el punto 0.5% no incluye sus itemsets ni sus reglas."
    )

with p3:
    st.subheader("Frecuencia de etiquetas individuales")
    items = items.copy()
    items["tipo"] = items["item"].str.split("=", n=1).str[0]
    tipo = st.selectbox("Tipo de etiqueta", ["Todos"] + sorted(items["tipo"].unique().tolist()))
    mostrados = items if tipo == "Todos" else items.loc[items["tipo"].eq(tipo)]
    top = mostrados.nlargest(15, "count").sort_values("count")
    fig = px.bar(
        top, x="count", y="item", orientation="h",
        labels={"count": "Transacciones", "item": "Etiqueta"},
    )
    st.plotly_chart(fig, width="stretch")
    st.subheader("Exploración de conjuntos frecuentes")
    itemsets = itemsets.copy()
    itemsets["tamano"] = itemsets["itemset"].str.split(" & ", regex=False).str.len()
    tam = st.selectbox("Tamaño del conjunto", sorted(itemsets["tamano"].unique().tolist()))
    sub = itemsets.loc[itemsets["tamano"].eq(tam)].nlargest(30, "freq")
    st.dataframe(sub[["itemset", "freq", "soporte"]], width="stretch", hide_index=True)
    st.caption(
        "Los conjuntos pertenecen al universo filtrado de 196,158 transacciones. "
        "La sede departamental corresponde a la entidad, no al lugar de ejecución."
    )

siguiente('pages/7_Reglas_Asociacion.py', 'Reglas')
