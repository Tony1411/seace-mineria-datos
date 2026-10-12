import math

import pandas as pd
import plotly.express as px
import streamlit as st

from utils import cargar_csv, encabezado, siguiente

st.title("Reglas de asociación — SEACE")

encabezado(
    '¿Qué características se asocian con que un proceso quede desierto o nulo?',
    'Con cero postores, DESIERTO sube de 12.88% a 35.45% (lift 2.75). En municipalidades con cero postores, NULO llega a 59.5% (lift 9.8). Son asociaciones, no causas.',
)
st.markdown(
    """**Pregunta:** ¿Qué combinaciones de características de los procesos aparecen
    conjuntamente con mayor frecuencia de la esperada?

    **Pipeline:** procesos SEACE → 196,158 transacciones por `release_id` →
    FP-Growth → conjuntos frecuentes → reglas → soporte, confianza y lift.

    Los resultados se calculan fuera de la aplicación. Los controles **filtran
    las reglas exportadas**, no reejecutan FP-Growth.
    """
)

reglas = cargar_csv("c", "reglas_asociacion.csv")
seleccionadas = cargar_csv("c", "reglas_seleccionadas.csv")

pestaña_reglas, pestaña_destacadas = st.tabs(
    ["Explorar reglas", "6 reglas destacadas"]
)

with pestaña_reglas:
    st.subheader("Filtros interactivos")
    c1, c2, c3 = st.columns(3)
    soporte_pct = c1.slider("Soporte mínimo (%)", 1.0, 20.0, 1.0, 0.5)
    confianza_pct = c2.slider("Confianza mínima (%)", 30, 100, 50, 5)
    lift_minimo = c3.slider("Lift mínimo", 1.0, 10.0, 1.5, 0.5)

    c4, c5 = st.columns(2)
    ocultar_triviales = c4.checkbox(
        "Ocultar reglas marcadas como cruce ley/procedimiento", value=True
    )
    cons_simple = c5.checkbox("Solo consecuentes de un ítem", value=True)

    objetivo = st.selectbox(
        "Consecuente de interés",
        ["Todos", "estado=DESIERTO", "estado=NULO", "estado=CONTRATADO"],
    )
    texto = st.text_input("Buscar texto en antecedente o consecuente (opcional)")

    df = reglas.loc[
        (reglas["soporte"] >= soporte_pct / 100)
        & (reglas["confianza"] >= confianza_pct / 100)
        & (reglas["lift"] >= lift_minimo)
    ].copy()

    if ocultar_triviales:
        df = df.loc[~df["trivial_ley_proc"]]
    if cons_simple:
        df = df.loc[df["k_cons"] == 1]
    if objetivo != "Todos":
        df = df.loc[df["consecuente"] == objetivo]
    if texto.strip():
        coincide = (
            df["antecedente"].str.contains(texto.strip(), case=False, regex=False, na=False)
            | df["consecuente"].str.contains(texto.strip(), case=False, regex=False, na=False)
        )
        df = df.loc[coincide]

    df = df.sort_values(["lift", "confianza"], ascending=[False, False])
    c1, c2, c3 = st.columns(3)
    c1.metric("Reglas coincidentes", f"{len(df):,}")
    c2.metric("Catálogo exportado", f"{len(reglas):,}")
    c3.metric("Cruces ley/procedimiento marcados", f"{int(reglas['trivial_ley_proc'].sum()):,}")

    st.caption(
        "Catálogo original restringido a soporte ≥ 1%, confianza ≥ 30% "
        "y lift ≥ 1.0. Reducir el filtro no recupera reglas no exportadas. "
        "Las métricas del catálogo general están redondeadas."
    )

    if df.empty:
        st.info("No se encontraron reglas con los filtros actuales.")
    else:
        pagina_size = 50
        paginas = max(1, math.ceil(len(df) / pagina_size))
        pagina = st.number_input("Página de resultados", min_value=1, max_value=paginas, value=1)
        offset = (pagina - 1) * pagina_size
        muestra = df.iloc[offset : offset + pagina_size].copy()
        muestra["soporte (%)"] = muestra["soporte"] * 100
        muestra["confianza (%)"] = muestra["confianza"] * 100
        st.dataframe(
            muestra[["antecedente", "consecuente", "soporte (%)", "confianza (%)", "lift"]].round(3),
            width="stretch",
            hide_index=True,
        )
        st.caption(f"Mostrando {offset + 1}–{min(offset + pagina_size, len(df))} de {len(df)} reglas.")

        st.subheader("Distribución de lift en las reglas filtradas")
        fig = px.histogram(
            df, x="lift", nbins=35,
            labels={"lift": "Lift", "count": "Número de reglas"},
        )
        fig.update_layout(yaxis_title="Número de reglas")
        st.plotly_chart(fig, width="stretch")

with pestaña_destacadas:
    st.markdown(
        """El notebook seleccionó 12 reglas candidatas automáticamente. Aquí se
        muestran las **6 primeras**, que hablan de procesos desiertos y nulos.
        Las otras 6 se omiten porque son casi tautológicas: relacionan
        `monto=protegido` con `postores=0`, o son reglas de 9 ítems que repiten
        el mismo conjunto. Siguen en el archivo `reglas_seleccionadas.csv`.
        **Las 6 mostradas tampoco son hallazgos independientes**: comparten condiciones.
        """
    )
    seleccionadas = seleccionadas.iloc[:6].reset_index(drop=True)
    idx = st.selectbox(
        "Regla destacada",
        range(len(seleccionadas)),
        format_func=lambda i: (
            f"{i + 1}. {str(seleccionadas.iloc[i]['antecedente'])[:65]}"
            f" → {str(seleccionadas.iloc[i]['consecuente'])[:40]}"
        ),
    )
    regla = seleccionadas.iloc[idx]
    st.code(f"{regla['antecedente']}\n     → {regla['consecuente']}", language=None)
    c1, c2, c3 = st.columns(3)
    c1.metric("Soporte", f"{regla['soporte'] * 100:.3f}%")
    c2.metric("Confianza", f"{regla['confianza'] * 100:.2f}%")
    c3.metric("Lift", f"{regla['lift']:.3f}")

    st.markdown(
        f"De las transacciones que reúnen el antecedente, "
        f"**{regla['confianza'] * 100:.2f}%** también reúnen "
        f"el consecuente. El lift es **{regla['lift']:.2f}** frente "
        f"a la frecuencia general del consecuente."
    )
    st.dataframe(
        seleccionadas[["antecedente", "consecuente", "soporte", "confianza", "lift"]],
        width="stretch", hide_index=True,
    )
    st.warning(
        "Una asociación no demuestra causalidad ni irregularidades. "
        "`postores=0` significa cero postores registrados, no necesariamente "
        "ausencia real de competencia. `ley=anterior` es una clasificación temporal."
    )

st.markdown(
    """### Interpretación y alcance
    - El universo de asociación comprende **196,158 transacciones**; se excluyeron
      13,582 procesos según los filtros documentados en el notebook.
    - Los cruces de ley y procedimiento pueden reflejar un cambio en las
      denominaciones y se pueden ocultar con el filtro de la página.
    - `estado=NULO` es una etiqueta de estado del proceso, no un dato faltante.
    - La asociación es descriptiva; no constituye un clasificador predictivo.
    """
)

siguiente('pages/10_Discusion_Critica.py', 'Discusión crítica')
