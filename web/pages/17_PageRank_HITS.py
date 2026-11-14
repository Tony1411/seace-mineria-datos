import pandas as pd
import plotly.express as px
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Parte IV · PageRank y HITS")

res = json_p2("p4_resumen.json")
g, pr, hi = res["grafo_pagerank"], res["pagerank"], res["hits"]
sens = csv_p2("pr_sensibilidad.csv")
por_beta = csv_p2("pr_por_beta.csv")

encabezado(
    "¿Qué proveedores concentran el mercado y cómo cambia ese ranking si se cambia el factor de amortiguamiento (β)?",
    f"PageRank sobre {g['nodos']:,} proveedores pone arriba a quienes ganan frente a rivales que también ganan. "
    f"El 1% de arriba ({pr['n_top1pct']} proveedores) reúne {100 * pr['masa_top1pct']:.1f}% del PageRank total. "
    f"El ranking de arriba es estable para β entre 0.50 y 0.95. Es una señal descriptiva, no una acusación.",
)

st.markdown(f"""
### Qué grafo se usa
- **Nodo:** un proveedor con al menos {g['parametros']['min_participaciones']} participaciones.
- **Arista A → B:** A ofertó y **no ganó**, y B **sí ganó** en el mismo proceso. El **peso** es en cuántos procesos pasó. Cada derrota es un voto: *B fue mejor que yo*.
- **Dead ends** (callejones sin salida): {g['dead_ends']:,} proveedores ({g['pct_dead_ends']}%) **nunca pierden**, así que no votan por nadie. Se manejan con la teletransportación.
- **Fórmula de clase:** `r = β·M·r + (1 − β)/N`. **β** es la probabilidad de seguir una arista; con probabilidad `1 − β` el caminante se teletransporta a un proveedor al azar.
""")

tab_beta, tab_top, tab_sens, tab_hits = st.tabs(["Ranking con β ajustable", "PageRank frente a victorias", "Sensibilidad y convergencia", "HITS: entidades y proveedores"])

with tab_beta:
    betas = sorted(por_beta.beta.unique())
    c1, c2 = st.columns([2, 1])
    beta = c1.select_slider("Factor de amortiguamiento β", options=betas, value=0.85,
                            help="Con β alto el caminante casi nunca se teletransporta y el rango se concentra más.")
    n_mostrar = c2.slider("Cuántos proveedores mostrar", 5, 25, 15)
    f = sens[sens.beta == beta].iloc[0]
    m = st.columns(4)
    m[0].metric("Parecido con β = 0.85", f"{f.spearman_vs_085:.4f}", help="Correlación de rangos (Spearman) entre este ranking y el de β = 0.85. 1 = idénticos.")
    m[1].metric("De los 10 primeros, iguales a β = 0.85", f"{int(f.top10_en_comun)} de 10")
    m[2].metric("PageRank del 1% de arriba", f"{100 * f.masa_top1pct:.1f}%", help="Qué parte del PageRank total reúne el 1% de proveedores con más rango.")
    m[3].metric("Iteraciones", f"{int(f.iteraciones)}", help="Pasos de la iteración de potencia hasta que r casi no cambia. Con β más alto hacen falta más.")

    top = por_beta[por_beta.beta == beta].sort_values("rango").head(n_mostrar).copy()
    base = por_beta[por_beta.beta == 0.85].set_index("ruc").rango
    top["rango_085"] = top.ruc.map(base).apply(lambda v: "fuera del top 25" if pd.isna(v) else str(int(v)))
    fig = px.bar(top.iloc[::-1], x="pr_veces_uniforme", y="nombre", orientation="h",
                 labels={"pr_veces_uniforme": "PageRank (veces el de un proveedor promedio)", "nombre": ""})
    fig.update_layout(height=max(320, 28 * n_mostrar), margin=dict(l=0, r=0, t=10, b=0))
    st.plotly_chart(fig, width="stretch")
    st.dataframe(top[["rango", "nombre", "ruc", "pr_veces_uniforme", "rango_085"]].rename(columns={
        "rango": "Rango", "nombre": "Proveedor", "ruc": "RUC", "pr_veces_uniforme": "PageRank (veces el promedio)", "rango_085": "Rango con β = 0.85"}),
        width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.** «PageRank en veces el promedio» dice cuántas veces más rango tiene un proveedor que uno típico (1 = típico).
Los RUC que no empiezan con 20 se muestran enmascarados y los nombres de personas naturales se reemplazan.
Estar arriba **no indica irregularidades**: puede ser una empresa grande, bien posicionada o especializada.
""")

with tab_top:
    t = csv_p2("pr_top.csv").copy()
    t["tasa_exito"] = (100 * t.tasa_exito).round(1)
    st.dataframe(t[["rango_pr", "nombre", "ruc", "pr_veces_uniforme", "n_participaciones", "n_adjudicaciones", "tasa_exito", "rango_victorias", "rivales_vencidos"]].rename(columns={
        "rango_pr": "Rango PageRank", "nombre": "Proveedor", "ruc": "RUC", "pr_veces_uniforme": "PageRank (veces el promedio)",
        "n_participaciones": "Procesos en que ofertó", "n_adjudicaciones": "Veces que ganó", "tasa_exito": "Tasa de éxito (%)", "rango_victorias": "Rango por victorias", "rivales_vencidos": "Rivales distintos que perdieron frente a él"}),
        width="stretch", hide_index=True)
    d = csv_p2("pr_dispersion.csv")
    d = d[d.n_adjudicaciones > 0]
    fig = px.scatter(d, x="n_adjudicaciones", y="pr_veces_uniforme", color="tasa_exito", log_x=True, log_y=True, opacity=0.6,
                     labels={"n_adjudicaciones": "Veces que ganó (escala log)", "pr_veces_uniforme": "PageRank (veces el promedio, escala log)", "tasa_exito": "Tasa de éxito"},
                     color_continuous_scale="Viridis")
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"""
**Cómo leerlo.** Cada punto es un proveedor (se muestran los 300 primeros y una muestra de 3,000 del resto).
PageRank **se parece a contar victorias** (correlación de rangos {pr['spearman_con_victorias']:.2f}), pero no es lo mismo:
- **Suben** los que, con pocas victorias, **vencieron a muchos rivales distintos** (ganaron procesos muy concurridos); además, el voto de un rival que pierde poco pesa más para quien le ganó.
- **Bajan** los que tienen **tasa de éxito cercana a 100%**: ganan procesos donde casi no hay rivales y reciben pocos votos.
""")

with tab_sens:
    s = sens.copy()
    s["convergio"] = s.convergio if "convergio" in s else "sí"
    st.dataframe(s.rename(columns={"beta": "β", "iteraciones": "Iteraciones", "convergio": "¿Convergió?", "spearman_vs_085": "Spearman vs β = 0.85",
                                   "top10_en_comun": "Top 10 en común", "top50_en_comun": "Top 50 en común",
                                   "masa_top1pct": "PageRank del 1% de arriba", "pr_maximo_veces_uniforme": "PageRank máximo (veces el promedio)"}),
                 width="stretch", hide_index=True)
    a, b = st.columns(2)
    f1 = px.line(sens, x="beta", y="masa_top1pct", markers=True, labels={"beta": "β", "masa_top1pct": "PageRank del 1% de arriba"})
    a.plotly_chart(f1, width="stretch")
    conv = csv_p2("pr_convergencia.csv")
    elegidos = st.multiselect("Valores de β a comparar en la convergencia", sorted(conv.beta.unique()), default=[0.5, 0.85, 0.95])
    f2 = px.line(conv[conv.beta.isin(elegidos)], x="iteracion", y="cambio", color=conv[conv.beta.isin(elegidos)].beta.astype(str), log_y=True,
                 labels={"iteracion": "Iteración", "cambio": "Cambio total entre iteraciones (escala log)", "color": "β"})
    b.plotly_chart(f2, width="stretch")
    st.markdown("""
**Cómo leerlo.**
- **Para β entre 0.50 y 0.95** el ranking de arriba casi no cambia (Spearman mayor a 0.99; entre 8 y 10 de los 10 primeros se mantienen).
- **Todos los β convergen**, pero con β = 0.95 hacen falta unas 300 iteraciones (con β = 0.85, 95). Un valor extremo como 0.99 exigiría más de mil y no se incluyó.
- **Cuanto mayor β**, más se concentra el rango en pocos proveedores y **más iteraciones** hacen falta: el error baja por un factor cercano a β en cada paso.
- Se usa **β = 0.85**, el valor de clase.
""")

with tab_hits:
    st.markdown(f"""
**HITS** da dos puntajes en un grafo con dirección **entidad → proveedor** (la entidad adjudicó al proveedor al menos una vez):
- **Authority (autoridad):** proveedor al que adjudican buenos *hubs*.
- **Hub (concentrador):** entidad que adjudica a buenas *authorities*.

Se calculó con iteración de potencia ({hi['iteraciones']} iteraciones) sobre {hi['entidades']:,} entidades y {hi['proveedores']:,} proveedores ({hi['enlaces']:,} enlaces).
La autoridad coincide con el primer vector singular de la matriz entidad×proveedor (coseno {hi['coseno_con_svd']}), es decir, con la **SVD** de clase.
""")
    a, b = st.columns(2)
    au = csv_p2("hits_autoridades.csv")
    a.markdown("**Proveedores con más autoridad**")
    a.dataframe(au[["rango_autoridad", "nombre", "ruc", "n_entidades", "rango_pr"]].rename(columns={
        "rango_autoridad": "Rango", "nombre": "Proveedor", "ruc": "RUC", "n_entidades": "Entidades", "rango_pr": "Rango PageRank"}), width="stretch", hide_index=True)
    hu = csv_p2("hits_hubs.csv")
    b.markdown("**Entidades con más hub**")
    b.dataframe(hu.rename(columns={"rango_hub": "Rango", "entidad": "Entidad", "entidad_tipo": "Tipo", "entidad_departamento": "Departamento", "n_proveedores": "Proveedores"}),
                width="stretch", hide_index=True)
    st.markdown(f"""
**Cómo leerlo.**
- Los **hubs** son entidades grandes que compran a muchísimos proveedores (hospitales, institutos de salud, defensa). Correlación de rangos con el número de proveedores: {hi['spearman_hub_vs_n_proveedores']:.2f}.
- Las **autoridades** tienen relación moderada con el número de entidades con que trabajan (correlación {hi['spearman_autoridad_vs_n_entidades']:.2f}): pesa **cuáles** entidades les adjudican, no solo cuántas.
- **PageRank y HITS responden preguntas distintas**: PageRank mira quién gana frente a quién; HITS mira quién compra a quién. Su correlación es baja ({hi['spearman_autoridad_vs_pagerank']:.2f}).
- Todo es una **señal descriptiva**; no prueba ni sugiere irregularidades.
""")

st.warning("Un PageRank o una autoridad alta **no indica irregularidades**: refleja volumen, tamaño o buena posición en la red. Sirve para elegir casos que una persona revise con más contexto.")

st.caption("Notebook: `P2_07_PageRank_HITS` (Spark: grafo de derrotas, iteración de potencia de PageRank y de HITS; verificado contra NetworkX y contra la SVD).")
siguiente("pages/18_Comunidades.py", "Comunidades")
