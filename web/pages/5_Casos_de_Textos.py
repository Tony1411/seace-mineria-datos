
import html
from difflib import SequenceMatcher

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import cargar_json, encabezado, siguiente


st.title("Casos de similitud y textos repetidos")

encabezado(
    '¿Qué textos se repiten y entre quiénes?',
    'El 96.6% de los pares casi iguales ocurre dentro de la misma entidad. Un solo texto genérico se repite en 550 procesos de una entidad.',
)

st.markdown("""
Exploración de descripciones de contratación similares o repetidas
en los datos del SEACE.

**Pipeline:** textos normalizados → similitud Jaccard →
identificación de pares → análisis de entidades y repeticiones.
""")


@st.cache_data
def cargar_casos():
    datos = cargar_json(
        "similitud", "casos_similares.json"
    )["datos"]

    df = pd.DataFrame(datos)
    df["jaccard"] = pd.to_numeric(
        df["jaccard"], errors="coerce"
    )
    return df


@st.cache_data
def cargar_repetidos():
    datos = cargar_json(
        "similitud", "grupos_repetidos.json"
    )["datos"]

    return pd.DataFrame(datos)


def resaltar_diferencias(texto_a, texto_b):
    palabras_a = str(texto_a).split()
    palabras_b = str(texto_b).split()

    comparador = SequenceMatcher(
        None, palabras_a, palabras_b,
        autojunk=False
    )

    partes_a = []
    partes_b = []

    for tipo, a1, a2, b1, b2 in comparador.get_opcodes():
        segmento_a = html.escape(
            " ".join(palabras_a[a1:a2])
        )
        segmento_b = html.escape(
            " ".join(palabras_b[b1:b2])
        )

        if tipo != "equal":
            if segmento_a:
                segmento_a = f"<mark>{segmento_a}</mark>"
            if segmento_b:
                segmento_b = f"<mark>{segmento_b}</mark>"

        if segmento_a:
            partes_a.append(segmento_a)

        if segmento_b:
            partes_b.append(segmento_b)

    return " ".join(partes_a), " ".join(partes_b)


tab_casos, tab_repetidos = st.tabs([
    "Textos similares",
    "Textos repetidos",
])


# ======================================================
# TAB 1: CASOS DE SIMILITUD
# ======================================================

with tab_casos:
    st.subheader("Exploración de pares similares")

    st.markdown("""
    **Pregunta:** ¿Qué tipos de procesos presentan
    descripciones muy similares, incluso entre
    distintas entidades o departamentos?
    """)

    df = cargar_casos()

    tipos = sorted(
        df["tipo_caso"].dropna().unique().tolist()
    )

    c1, c2 = st.columns(2)

    with c1:
        tipo = st.selectbox(
            "Tipo de caso",
            ["Todos"] + tipos,
        )

    with c2:
        umbral = st.slider(
            "Jaccard mínimo",
            min_value=0.80,
            max_value=1.00,
            value=0.80,
            step=0.01,
        )

    filtrado = df[df["jaccard"] >= umbral].copy()

    if tipo != "Todos":
        filtrado = filtrado[
            filtrado["tipo_caso"] == tipo
        ]

    filtrado = filtrado.sort_values(
        "jaccard", ascending=False
    ).reset_index(drop=True)

    st.metric(
        "Pares en la muestra filtrada",
        len(filtrado)
    )

    st.caption(
        "La muestra contiene 60 pares seleccionados "
        "de forma balanceada (20 por tipo). "
        "No representa la distribución poblacional."
    )

    if filtrado.empty:
        st.info("No se encontraron pares para estos filtros.")
    else:
        indice = st.selectbox(
            "Selecciona un par para inspeccionar",
            options=list(range(len(filtrado))),
            format_func=lambda i: (
                f"Par {i + 1} — "
                f"Jaccard {filtrado.iloc[i]['jaccard']:.3f}"
            ),
        )

        par = filtrado.iloc[indice]

        st.metric(
            "Similitud de Jaccard",
            f"{par['jaccard']:.4f}"
        )

        texto_a, texto_b = resaltar_diferencias(
            par["texto_a"],
            par["texto_b"],
        )

        col_a, col_b = st.columns(2)

        with col_a:
            st.markdown("#### Texto A")

            st.markdown(
                texto_a,
                unsafe_allow_html=True,
            )

            st.write("**Entidad:**", par["entidad_a"])
            st.write(
                "**Departamento:**",
                par["departamento_a"]
            )
            st.write(
                "**Primera publicación:**",
                par["primera_fecha_a"]
            )
            st.write(
                "**Número de procesos:**",
                par["n_procesos_a"]
            )

        with col_b:
            st.markdown("#### Texto B")

            st.markdown(
                texto_b,
                unsafe_allow_html=True,
            )

            st.write("**Entidad:**", par["entidad_b"])
            st.write(
                "**Departamento:**",
                par["departamento_b"]
            )
            st.write(
                "**Primera publicación:**",
                par["primera_fecha_b"]
            )
            st.write(
                "**Número de procesos:**",
                par["n_procesos_b"]
            )

        st.caption(
            "Las palabras resaltadas representan "
            "diferencias textuales entre ambos textos."
        )

    st.markdown("""
    ### Interpretación

    La similitud textual permite identificar
    descripciones casi iguales dentro de una misma
    entidad o entre diferentes entidades.

    Una alta similitud **no demuestra duplicidad
    de procesos ni irregularidades**: distintas
    contrataciones pueden compartir descripciones.
    """)


# ======================================================
# TAB 2: TEXTOS REPETIDOS
# ======================================================

with tab_repetidos:
    st.subheader("Descripciones más repetidas")

    st.markdown("""
    **Pregunta:** ¿Qué descripciones aparecen
    repetidamente en procesos de contratación
    y cuántas entidades diferentes las utilizan?
    """)

    df = cargar_repetidos()

    df["n_procesos"] = pd.to_numeric(
        df["n_procesos"], errors="coerce"
    )
    df["n_entidades"] = pd.to_numeric(
        df["n_entidades"], errors="coerce"
    )

    c1, c2 = st.columns(2)

    with c1:
        top_n = st.slider(
            "Número de textos a visualizar",
            min_value=5,
            max_value=30,
            value=15,
            step=5,
        )

    with c2:
        solo_varias = st.checkbox(
            "Solo textos usados por varias entidades",
            value=False,
        )

    filtrado = df.copy()

    if solo_varias:
        filtrado = filtrado[
            filtrado["n_entidades"] > 1
        ]

    filtrado = filtrado.sort_values(
        "n_procesos", ascending=False
    ).head(top_n).copy()

    filtrado = filtrado.reset_index(drop=True)

    if filtrado.empty:
        st.info("No hay textos para los filtros seleccionados.")
    else:
        filtrado["etiqueta"] = [
            f"{i + 1}. {str(texto)[:55]}"
            for i, texto in enumerate(filtrado["texto"])
        ]

        fig = px.bar(
            filtrado.sort_values("n_procesos"),
            x="n_procesos",
            y="etiqueta",
            orientation="h",
            hover_data=[
                "texto",
                "n_entidades",
                "n_departamentos",
            ],
            labels={
                "n_procesos": "Número de procesos",
                "etiqueta": "Descripción",
            },
            title="Descripciones más frecuentes",
            height=max(450, len(filtrado) * 36),
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

        st.subheader("Examinar una descripción")

        indice = st.selectbox(
            "Selecciona un texto repetido",
            options=list(range(len(filtrado))),
            format_func=lambda i: (
                f"{i + 1}. "
                f"{str(filtrado.iloc[i]['texto'])[:75]}"
            ),
        )

        fila = filtrado.iloc[indice]

        st.write(fila["texto"])

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Procesos",
            int(fila["n_procesos"])
        )
        c2.metric(
            "Entidades",
            int(fila["n_entidades"])
        )
        c3.metric(
            "Departamentos",
            int(fila["n_departamentos"])
        )

        st.write("**Entidad principal:**", fila["entidad"])
        st.write("**Departamento:**", fila["departamento"])
        st.write("**Primera fecha:**", fila["primera_fecha"])
        st.write("**Última fecha:**", fila["ultima_fecha"])

        monto = pd.to_numeric(
            fila["valor_total_pen"], errors="coerce"
        )

        if pd.notna(monto):
            st.metric(
                "Valor total registrado",
                f"S/ {monto:,.2f}"
            )

    st.markdown("""
    ### Interpretación

    Las descripciones repetidas permiten estudiar
    patrones de reutilización de textos en las
    contrataciones públicas.

    La utilización de una misma descripción por
    múltiples entidades constituye un hallazgo
    descriptivo, pero no implica necesariamente
    que los procesos sean duplicados.

    El análisis está limitado a los 100 textos
    repetidos proporcionados en los artefactos.
    """)

siguiente('pages/6_ANN.py', 'Vecinos aproximados (ANN)')
