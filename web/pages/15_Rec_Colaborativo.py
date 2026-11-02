import plotly.graph_objects as go
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2

st.title("Proyecto 2 · Recomendador colaborativo")

vk = csv_p2("vecindario_k.csv")            # item–item
vu = csv_p2("vecindario_user_k.csv")       # user–user
va_ = csv_p2("vecindario_variantes.csv")
aa = csv_p2("als_alpha.csv")
al = csv_p2("als_parametros.csv")
ref_r = vk["referencia_recall@10"].iloc[0]
mejor = al.sort_values("recall@10", ascending=False).iloc[0]

encabezado(
    "¿Quiénes contratan a los mismos proveedores también contratan a otros en común? ¿Se puede usar eso para recomendar?",
    f"Sí. En la validación (el 20% más reciente de train), el modelo ALS acierta {100 * mejor['recall@10']:.1f}% de los proveedores nuevos en su top-10, "
    f"frente a {100 * ref_r:.1f}% de recomendar los más populares (≈{mejor['recall@10'] / ref_r:.0f} veces más). El vecindario llega a {100 * vu['recall@10'].max():.1f}% (entre entidades) y {100 * vk['recall@10'].max():.1f}% (entre proveedores).",
)

st.markdown("""
### Tres formas de usar «quién contrata a quién»
- **Vecindario item–item (entre proveedores):** dos proveedores son parecidos si tienen las mismas entidades. Se guardan los **K vecinos** más parecidos de cada proveedor
  y una entidad recibe los vecinos de los proveedores que ya tiene.
- **Vecindario user–user (entre entidades):** dos entidades son parecidas si contratan a los mismos proveedores. Se guardan las **K entidades vecinas** de cada entidad
  y se le recomienda lo que contratan sus vecinas y ella todavía no.
- **ALS (Spark MLlib):** da a cada entidad y a cada proveedor un vector de **r factores**; si se «encajan» (producto punto alto), se recomienda.
  Tomar el par como **interacción implícita** significa que existir indica interés y no existir solo indica «no se sabe».

### Cómo se mide
Se ocultan los pares más recientes y se mira si el modelo los adivina entre sus 10 primeras recomendaciones.
**Recall@10:** de los proveedores nuevos que la entidad sí contrató, qué fracción quedó en el top-10 (1 = todos).
Los parámetros se eligen aquí, **sin usar el test**.
""")

tab_v, tab_u, tab_a, tab_s = st.tabs(["Vecindario item–item (K)", "Vecindario user–user (K)", "ALS (factores)", "¿Qué similitud?"])

with tab_v:
    k = st.select_slider("Vecinos por proveedor (K)", options=[int(v) for v in vk.vecinos], value=int(vk.sort_values("recall@10").vecinos.iloc[-1]))
    f = vk[vk.vecinos == k].iloc[0]
    c = st.columns(2)
    c[0].metric("Recall@10", f"{f['recall@10']:.3f}", f"{f['recall@10'] - ref_r:+.3f} frente a populares")
    c[1].metric("Referencia (populares)", f"{ref_r:.3f}", help="Recall@10 de recomendar siempre los proveedores con más entidades.")
    fig = go.Figure()
    fig.add_scatter(x=vk.vecinos, y=vk["recall@10"], mode="lines+markers", name="Recall@10")
    fig.add_hline(y=ref_r, line_dash="dot", annotation_text="populares (recall)")
    fig.add_vline(x=k, line_dash="dash")
    fig.update_layout(xaxis_title="Vecinos por proveedor (K)", yaxis_title="Métrica", xaxis_type="log")
    st.plotly_chart(fig, width="stretch")
    st.markdown("Con pocos vecinos las recomendaciones repiten lo que la entidad ya compra; con más vecinos mejora despacio y se frena (el mejor K está dentro de la rejilla, no en su borde). Es mejor que populares, pero lejos de ALS.")

with tab_u:
    ku = st.select_slider("Entidades vecinas por entidad (K)", options=[int(v) for v in vu.vecinos], value=int(vu.sort_values("recall@10").vecinos.iloc[-1]))
    f = vu[vu.vecinos == ku].iloc[0]
    c = st.columns(2)
    c[0].metric("Recall@10", f"{f['recall@10']:.3f}", f"{f['recall@10'] - ref_r:+.3f} frente a populares")
    c[1].metric("Referencia (populares)", f"{ref_r:.3f}")
    fig = go.Figure()
    fig.add_scatter(x=vu.vecinos, y=vu["recall@10"], mode="lines+markers", name="Recall@10")
    fig.add_hline(y=ref_r, line_dash="dot", annotation_text="populares (recall)")
    fig.add_vline(x=ku, line_dash="dash")
    fig.update_layout(xaxis_title="Entidades vecinas (K)", yaxis_title="Métrica", xaxis_type="log")
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"""
- Con **pocas entidades vecinas** (K = 5) se tiene muy poca información; con **muchas** se mezclan entidades poco parecidas. El mejor K está en el medio: **K = {int(vu.sort_values('recall@10').vecinos.iloc[-1])}**.
- **User–user rinde bastante más que item–item** en la validación ({vu['recall@10'].max():.3f} frente a {vk['recall@10'].max():.3f} de recall@10). En clase suele pasar al revés. En la página siguiente (pestaña «¿Qué tan seguro?») se comprueba por qué: user–user acierta sobre todo con proveedores grandes y conocidos.
""")

with tab_a:
    a, b = st.columns(2)
    r = a.select_slider("Factores (r)", options=sorted(int(v) for v in al.factores.unique()), value=int(mejor.factores))
    reg = b.select_slider("Regularización", options=sorted(al.regularizacion.unique()), value=float(mejor.regularizacion))
    f = al[(al.factores == r) & (al.regularizacion == reg)].iloc[0]
    c = st.columns(2)
    c[0].metric("Recall@10", f"{f['recall@10']:.3f}", f"{f['recall@10'] - ref_r:+.3f} frente a populares")
    c[1].metric("Referencia (populares)", f"{ref_r:.3f}")
    fig = go.Figure()
    for rg in sorted(al.regularizacion.unique()):
        s = al[al.regularizacion == rg].sort_values("factores")
        fig.add_scatter(x=s.factores, y=s["recall@10"], mode="lines+markers", name=f"regularización {rg:g}")
    fig.add_hline(y=ref_r, line_dash="dot", annotation_text="populares")
    fig.add_vline(x=r, line_dash="dash")
    fig.update_layout(xaxis_title="Factores (r)", yaxis_title="Recall@10", xaxis_type="log")
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"""
- **Más factores = más detalle** del gusto de cada entidad, pero la mejora se frena: de 64 a 128 factores el recall sube poco.
- **Regularización** (castigo a factores grandes): entre 0.01 y 1 cambia poco el recall (menos de 0.01 con 16 a 64 factores).
- **Con 256 factores el modelo rinde peor** (posible sobreajuste): el mejor número de factores está dentro de la rejilla. Con regularización 10 el modelo se destruye (recall menor a 0.01): castiga demasiado.
- **Alpha** (confianza que se da a cada interacción observada): se probó 1, 10 y 40 con la mejor combinación. Gana **alpha = {float(aa.sort_values('recall@10').alpha.iloc[-1]):g}** (recall {aa['recall@10'].max():.3f}; con 1: {float(aa[aa.alpha == 1]['recall@10'].iloc[0]):.3f}, con 40: {float(aa[aa.alpha == 40]['recall@10'].iloc[0]):.3f}).
- Elegido: **{int(mejor.factores)} factores, regularización {mejor.regularizacion:g} y alpha {float(aa.sort_values('recall@10').alpha.iloc[-1]):g}** (mejor recall@10 en la validación).
- Valor de cada par: `log(1 + n° de adjudicaciones)`, para que 200 contratos no pesen 200 veces más que 1.
""")

with tab_s:
    st.markdown("""
En clase se vieron tres similitudes: **coseno**, **Jaccard** y **Pearson**. Aquí se compararon con los mismos datos (mismo K, validación):
- **Coseno:** entidades en común ÷ √(entidades de A · entidades de B).
- **Jaccard:** entidades en común ÷ entidades de A o de B.
- **Pearson:** correlación entre dos columnas de ceros y unos (centrada).
""")
    t = va_.rename(columns={"forma": "Forma", "similitud": "Similitud", "vecinos": "K", "recall@10": "Recall@10"})
    st.dataframe(t, hide_index=True, width="stretch")
    st.markdown("""
- En **item–item** el coseno es la mejor. En **user–user** las tres dan casi lo mismo.
- Pearson sirve cuando hay calificaciones (1 a 5) y cada persona califica distinto. Aquí los valores son «existe / no existe», así que centrar casi no aporta.
""")

with st.expander("Límites"):
    st.markdown("""
- Estas cifras son de la **validación dentro de train**. El resultado final sobre el test y la comparación con el híbrido están en la página siguiente.
- Solo hay recomendaciones para proveedores y entidades que ya tienen historia (el «arranque en frío» no se resuelve con este método; ahí ayuda el contenido).
- Recomendar «quién se parece a quién» puede reproducir lo que ya existe: proveedores ya populares tienden a seguir apareciendo.
""")

st.caption("Notebook: `P2_05_Recomendador_Colaborativo` (NumPy y Spark MLlib ALS). Los controles muestran experimentos ya calculados, no vuelven a entrenar.")
siguiente("pages/16_Evaluacion_Hibrido.py", "Evaluación, híbrido y sustitutos")
