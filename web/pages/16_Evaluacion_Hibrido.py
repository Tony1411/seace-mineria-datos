import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Evaluación, híbrido, sustitutos y afinidades inusuales")

ev = csv_p2("eval_resultados.csv")
al = csv_p2("hibrido_alfa.csv")
ic = csv_p2("eval_ic.csv"); dif = csv_p2("eval_diferencias.csv"); cob = csv_p2("cobertura.csv")
sem = csv_p2("als_semillas.csv"); dg = csv_p2("diagnostico_grado.csv"); rep_ev = json_p2("reporte_evaluacion.json")
sus = json_p2("sustitutos.json")
sm = sus["meta"]

encabezado(
    "¿Qué proveedores son sustitutos entre sí para una misma entidad o categoría, y qué afinidades entidad–proveedor son inusuales?",
    f"Los proveedores parecidos por contenido comparten entidad en {sm['vecinos_comparten_entidad_pct']}% de los casos (al azar: {sm['azar_comparten_entidad_pct']}%) "
    f"y se presentan a los mismos procesos en {sm['vecinos_compitieron_pct']}% (al azar: {sm['azar_compitieron_pct']}%): son sustitutos funcionales reales. "
    "Las afinidades inusuales son sobre todo servicios de apoyo (internet, vigilancia, limpieza) en entidades que compran otras cosas: pistas para revisar, no irregularidades.",
)

tabs = st.tabs(["Modelos en el test", "¿Qué tan seguro?", "Híbrido (α)", "Sustitutos", "Afinidades inusuales", "Ejemplos"])

# ------------------------------------------------------------ modelos
with tabs[0]:
    st.markdown("""
Evaluación sobre el **test** (pares nuevos desde 2026-03-01): 4,926 pares en 1,331 entidades. Se mira el top-*k* de cada entidad.
**Precisión@k:** de los *k* recomendados, qué fracción contrató. **Recall@k:** de los proveedores nuevos que contrató, qué fracción estaba en el top-*k*.
""")
    k = st.radio("Top-k", [5, 10, 20], index=1, horizontal=True)
    metrica = st.radio("Métrica", ["recall", "precision"], horizontal=True, format_func=lambda x: {"recall": "Recall", "precision": "Precisión"}[x])
    t = ev[(ev.segmento == "todas") & (ev.k == k)]
    fig = px.bar(t, x="modelo", y=metrica, text=t[metrica].map(lambda v: f"{v:.3f}"), labels={"modelo": "", metrica: f"{metrica}@{k}"})
    st.plotly_chart(fig, width="stretch")
    pop = float(t[t.modelo.str.startswith("populares")][metrica].iloc[0])
    st.caption(f"Referencia: «populares» = {pop:.3f}. ALS es {float(t[t.modelo == 'ALS'][metrica].iloc[0]) / pop:.1f} veces mejor en este indicador.")

    st.subheader("Según cuántos proveedores tenía la entidad en train (recall@10)")
    s = ev[(ev.segmento != "todas") & (ev.k == 10)]
    orden = list(dict.fromkeys(s.segmento))
    fig = px.bar(s, x="segmento", y="recall", color="modelo", barmode="group", category_orders={"segmento": orden}, labels={"segmento": "Grupo de entidades", "recall": "Recall@10"})
    st.plotly_chart(fig, width="stretch")
    st.markdown("""
- ALS gana en los tres grupos; el vecindario user–user (entre entidades) queda segundo. El contenido supera a «populares» también en entidades con poca historia (recall 0.111 frente a 0.017).
- Las entidades con muchos proveedores son más difíciles: hay más entre qué elegir.
- Los valores absolutos son bajos (entre ~9,800 proveedores se intenta adivinar con quién contratará una entidad en pocos meses); importa cuánto mejor es cada modelo que la referencia.
""")

# ------------------------------------------------------------ incertidumbre
with tabs[1]:
    st.markdown("""
Con 1,331 entidades, una diferencia chica puede ser azar. Tres comprobaciones:
- **Intervalo de confianza del 95% (bootstrap):** se remuestrean las entidades con reemplazo 1,000 veces y se recalcula el promedio. Si dos intervalos no se tocan, la diferencia es creíble.
- **Diferencia entre dos modelos:** se remuestrean las **mismas** entidades para ambos y se mira el intervalo de la diferencia; si no incluye 0, los modelos se distinguen.
- **Semillas de ALS:** ALS parte de números al azar; se entrenó 5 veces con semillas distintas.
""")
    t = ic.copy()
    fig = go.Figure(go.Bar(x=t.modelo, y=t["recall@10"], error_y=dict(type="data", symmetric=False, array=t.recall_ic_alto - t["recall@10"], arrayminus=t["recall@10"] - t.recall_ic_bajo),
                           text=t["recall@10"].map(lambda v: f"{v:.3f}"), textposition="outside"))
    fig.update_layout(title="Recall@10 con intervalo de confianza del 95%", yaxis_title="Recall@10", xaxis_title="")
    st.plotly_chart(fig, width="stretch")
    d = dif.rename(columns={"comparacion": "Comparación", "dif_recall@10": "Diferencia de recall@10", "ic_bajo": "Intervalo (bajo)", "ic_alto": "Intervalo (alto)", "distinguible": "¿Distinguible?"})
    d["¿Distinguible?"] = d["¿Distinguible?"].map({True: "Sí", False: "No"})
    st.dataframe(d, hide_index=True, width="stretch")
    st.markdown(f"""
- **ALS, user–user y el híbrido** están por encima de item–item y contenido de forma creíble. **Item–item y contenido no se distinguen entre sí.** ALS le gana a user–user, pero por poco (intervalo de la diferencia: {dif.iloc[1].ic_bajo:.3f} a {dif.iloc[1].ic_alto:.3f}).
- **Semillas de ALS:** recall@10 promedio **{sem['recall@10'].mean():.4f}**, desviación {sem['recall@10'].std():.4f}, entre {sem['recall@10'].min():.4f} y {sem['recall@10'].max():.4f}. El resultado no depende de la semilla.
""")
    st.subheader("Cobertura y popularidad")
    st.markdown("**Cobertura:** de los proveedores del universo, cuántos distintos aparecen en el top-10 de alguna entidad. **% en el top-100 populares:** qué parte de las recomendaciones son los 100 proveedores con más entidades.")
    c_ = cob.rename(columns={"modelo": "Modelo", "proveedores_distintos": "Proveedores distintos", "cobertura_pct": "Cobertura (%)", "pct_recomendaciones_en_top100_populares": "% en el top-100 populares"})
    st.dataframe(c_, hide_index=True, width="stretch")
    st.caption("«Populares» recomienda solo 19 proveedores distintos. User–user es el más concentrado entre los modelos personalizados: acertar más no significa recomendar con más variedad.")
    st.subheader("¿Por qué user–user supera a item–item?")
    st.markdown("Hipótesis inicial: item–item sufre porque cada proveedor atiende a pocas entidades (mediana 3; el 46% tiene 2 o menos). Si fuera así, debería quedar peor con esos proveedores. Se separaron los pares nuevos del test según cuántas entidades tenía el proveedor en train:")
    g = dg.pivot(index="grupo_del_proveedor", columns="modelo", values="recall@10").loc[["≤2 entidades", "3 a 9 entidades", "10 o más entidades"]]
    n_ = dg.groupby("grupo_del_proveedor").pares_nuevos.first()
    g.insert(0, "Pares nuevos", [int(n_[i]) for i in g.index]); g.index.name = "Proveedor a adivinar"
    st.dataframe(g.round(3), width="stretch")
    fig = px.bar(dg, x="grupo_del_proveedor", y="recall@10", color="modelo", barmode="group", category_orders={"grupo_del_proveedor": ["≤2 entidades", "3 a 9 entidades", "10 o más entidades"]},
                 labels={"grupo_del_proveedor": "Entidades que tenía el proveedor en train", "recall@10": "Recall@10"})
    st.plotly_chart(fig, width="stretch")
    st.markdown("""
**La hipótesis no se cumple:** item–item es *mejor* con proveedores de 2 o menos entidades. **User–user gana porque acierta con los proveedores grandes y conocidos** (con 10 o más entidades llega a 0.250, incluso sobre ALS) y es muy débil con los pequeños.
Va de la mano con la popularidad: 46% de su top-10 son los 100 proveedores más populares (ALS: 19%; item–item: 12%). ALS gana en total porque es el único que rinde bien en los tres grupos.
""")

# ------------------------------------------------------------ híbrido
with tabs[2]:
    st.markdown("""
**Híbrido = α · ALS + (1 − α) · contenido**, con cada puntaje normalizado por entidad para poder sumarlos. α = 0 es solo contenido; α = 1 es solo ALS.
El α se elige con la **validación dentro de train**, promediando **tres cortes** (70/30, 80/20 y 90/10); el test no interviene.
""")
    alfa = st.select_slider("α (peso de ALS)", options=[float(a) for a in al.alfa], value=0.1)
    f = al[al.alfa == alfa].iloc[0]
    c = st.columns(2)
    c[0].metric("Validación · recall@10", f"{f['val_recall@10']:.3f}")
    c[1].metric("Test · recall@10", f"{f['test_recall@10']:.3f}")
    fig = go.Figure()
    fig.add_scatter(x=al.alfa, y=al["val_recall@10"], mode="lines+markers", name="Validación (con eso se elige α)")
    fig.add_scatter(x=al.alfa, y=al["test_recall@10"], mode="lines+markers", name="Test (solo para informar)")
    fig.add_vline(x=alfa, line_dash="dash")
    fig.update_layout(xaxis_title="α (peso de ALS)", yaxis_title="Recall@10")
    st.plotly_chart(fig, width="stretch")
    vv = rep_ev["validacion_vs_test"]; v_ = vv["validación (corte 80/20)"]; t_ = vv["test"]
    st.warning("**Resultado honesto:** los tres cortes de validación eligen el mismo α = 0.1, pero en el test lo mejor está en α ≈ 0.6 (recall 0.152 frente a 0.136 de ALS solo). "
               "Con el α elegido, el híbrido (0.111) **no supera a ALS solo** y la diferencia es creíble. Elegir α mirando el test sería trampa, por eso no se hizo. "
               "Mezclar parece ayudar entre α = 0.4 y 0.8, pero esa mejora no se confirmó con un criterio válido.")
    st.markdown(f"""
**¿Por qué la validación y el test eligen distinto?** Los proveedores que hay que adivinar en la validación tienen **menos historia** que los del test:
mediana de {v_['mediana_entidades_del_proveedor']:.0f} entidades frente a {t_['mediana_entidades_del_proveedor']:.0f}, y {v_['pct_proveedor_con_2_o_menos_entidades']}% con 2 o menos frente a {t_['pct_proveedor_con_2_o_menos_entidades']}%.
El contenido no necesita historia, así que ayuda más en la validación; ALS sí la necesita y rinde mejor en el test. Es una explicación coherente con los números, no una prueba.
""")

# ------------------------------------------------------------ sustitutos
with tabs[3]:
    st.markdown(f"""
Dos proveedores son **sustitutos** si venden cosas muy parecidas (texto de los procesos que ganan) y además coinciden en los mismos lugares.
Para cada proveedor se toman sus 10 vecinos por contenido ({sm['pares_vecinos']:,} pares) y se mira:
""")
    c = st.columns(2)
    c[0].metric("Comparten al menos una entidad", f"{sm['vecinos_comparten_entidad_pct']}%", f"azar: {sm['azar_comparten_entidad_pct']}%", delta_color="off")
    c[1].metric("Se presentaron a los mismos procesos", f"{sm['vecinos_compitieron_pct']}%", f"azar: {sm['azar_compitieron_pct']}%", delta_color="off")
    sc = csv_p2("sustitutos_categoria.csv")
    st.markdown("**Por categoría principal del proveedor** (la que más aparece en sus participaciones):")
    st.dataframe(sc.rename(columns={"categoria": "Categoría", "pares": "Pares de vecinos", "similitud_mediana": "Similitud mediana",
                                    "comparten_entidad_pct": "Comparten entidad (%)", "compitieron_pct": "Mismos procesos (%)"}), hide_index=True, width="stretch")
    st.caption("En los tres rubros es mucho mayor que el azar (2.8% y 1.4%). Es más alto en bienes y más bajo en obras.")
    provs = sus["proveedores"]
    i = st.selectbox("Proveedor (los 150 con más entidades)", range(len(provs)), format_func=lambda i: f"{provs[i]['proveedor']} · {provs[i]['entidades']} entidades")
    p = provs[i]
    st.markdown(f"**{p['proveedor']}** — {p['entidades']} entidades · vende: _{p['palabras_clave']}_")
    t = pd.DataFrame(p["sustitutos"]).rename(columns={"nombre": "Sustituto probable", "similitud": "Similitud de contenido", "entidades_en_comun": "Entidades en común",
                                                      "procesos_en_comun": "Procesos en común", "entidades": "Sus entidades", "palabras_clave": "Qué vende"})
    st.dataframe(t, width="stretch", hide_index=True)
    st.markdown("""
- **Similitud de contenido:** coseno entre los textos (0 a 1).  **Entidades en común:** a cuántas entidades les adjudicaron ambos.  **Procesos en común:** a cuántos procesos se presentaron los dos como postores.
- Son sustitutos **funcionales** (la entidad podría haber elegido a cualquiera). Competir en muchos procesos es lo esperable en un rubro con pocos oferentes; no indica acuerdo entre ellos.
""")

# ------------------------------------------------------------ afinidades
with tabs[4]:
    af = csv_p2("afinidades_inusuales.csv")
    st.markdown("""
**Afinidad** de un par (entidad, proveedor) = parecido entre lo que vende ese proveedor y lo que venden **todos los demás** proveedores de esa entidad (0 = nada que ver; 1 = igual).
Son «inusuales» los pares del **2% con menor afinidad** (≤ 0.06; la mediana es 0.256). Aquí se muestran los 200 de mayor monto.
""")
    tipos = sorted(af.tipo_entidad.dropna().unique())
    a, b = st.columns(2)
    sel = a.multiselect("Tipo de entidad", tipos, default=tipos)
    monto = b.slider("Monto mínimo adjudicado (S/)", 0, int(af.monto_total.max()), 0, step=100000)
    d = af[af.tipo_entidad.isin(sel) & (af.monto_total >= monto)]
    st.caption(f"{len(d)} de {len(af)} pares")
    cols = {"entidad": "Entidad", "proveedor": "Proveedor", "afinidad": "Afinidad", "monto_total": "Monto adjudicado (S/)", "n_adjudicaciones": "Adjudicaciones",
            "que_vende_el_proveedor": "Qué vende el proveedor", "que_compra_la_entidad": "Qué compra la entidad (sus proveedores principales)"}
    st.dataframe(d[list(cols)].rename(columns=cols), width="stretch", hide_index=True)
    st.warning("Un par raro **para el modelo** no es necesariamente raro **para el negocio**: casi siempre son servicios de apoyo (internet, seguridad, limpieza, pasajes) o insumos "
               "(p. ej., cloro para una empresa de agua) en entidades cuyos otros proveedores venden algo distinto. Sirve para decidir qué mirar primero, no para concluir nada. "
               "Además, el texto del proveedor incluye lo que ganó en esa misma entidad, así que la afinidad real tiende a ser algo menor.")

# ------------------------------------------------------------ ejemplos
with tabs[5]:
    ej = json_p2("ejemplos_recomendaciones.json")
    mt = ej["meta"]
    st.markdown(f"Recomendaciones del híbrido (α = {mt['alfa']}) a entidades con 5 a 60 proveedores y al menos un acierto en su top-{mt['k']} "
                f"({mt['entidades_con_acierto']} de {mt['entidades_evaluables']} entidades evaluables). **Acierto** = la entidad sí contrató a ese proveedor en el test.")
    ejemplos = ej["ejemplos"]
    i = st.selectbox("Entidad", range(len(ejemplos)), format_func=lambda i: ejemplos[i]["entidad"])
    e = ejemplos[i]
    st.markdown(f"**{e['entidad']}** · {e['tipo']} · {e['departamento']} · {e['proveedores_en_train']} proveedores en train · {e['contrataciones_nuevas_en_test']} contrataciones nuevas en el test")
    a, b = st.columns(2)
    with a:
        st.markdown("**Ya trabajaba con** (top 5 por adjudicaciones)")
        for p in e["proveedores_actuales"]:
            st.markdown(f"- {p['nombre']} — {p['n_adjudicaciones']} adj.  \n  <small>{p['palabras_clave']}</small>", unsafe_allow_html=True)
    with b:
        st.markdown("**Recomendados (top 10)**")
        for p in e["recomendados"]:
            st.markdown(f"- {'✅' if p['acierto'] else '▫️'} {p['nombre']}  \n  <small>{p['palabras_clave']}</small>", unsafe_allow_html=True)

with st.expander("Límites"):
    st.markdown("""
- El test cubre pocos meses (desde 2026-03-01); las métricas pueden cambiar con más datos. Se evaluaron 4,926 de 10,303 pares del test: 5,374 ya existían en train y 3 son de 2 entidades que quedaron sin historia (arranque en frío).
- Es una sola partición temporal: los intervalos miden el azar al elegir entidades, no el cambio de periodo.
- Los consorcios (RUC de 7 dígitos) quedan fuera. Un proveedor con pocos procesos tiene un perfil de texto poco estable.
- Todo es una **señal descriptiva para revisar**; no prueba irregularidades.
""")

st.caption("Notebook: `P2_06_Evaluacion_Hibrido`. Los controles muestran resultados precalculados.")
siguiente("pages/10_Discusion_Critica.py", "Discusión crítica")
