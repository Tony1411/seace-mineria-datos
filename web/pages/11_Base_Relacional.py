import pandas as pd
import plotly.express as px
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import json_p2

st.title("Proyecto 2 · Base relacional entidad–proveedor")

r = json_p2("reporte_base.json")
emb, uni = r["embudo_adjudicaciones"], r["universo"]

encabezado(
    "¿Con qué datos se puede estudiar quién contrata a quién, y cuántos se pierden al armar esa relación?",
    f"De {emb['adjudicaciones_total']:,} adjudicaciones, {emb['usables_con_ruc_real']:,} "
    f"({100 * emb['usables_con_ruc_real'] / emb['adjudicaciones_total']:.0f}%) tienen un proveedor identificable. "
    f"El 22% son consorcios, que quedan fuera. La matriz final tiene {uni['proveedores']:,} proveedores × "
    f"{uni['entidades']:,} entidades y solo el {uni['densidad_pct']:.2f}% de sus celdas tiene datos.",
)

st.markdown("""
### Qué se hizo
Se parte de las tablas del Proyecto 1 (Parquet) y se arma, con **Spark**, la relación **entidad × proveedor**:
cuántas veces y por cuánto dinero una entidad le adjudicó a un proveedor. Es la base de todo el Proyecto 2
(grafo, agrupamiento y recomendación).

- **Corte en el tiempo:** lo anterior al **{corte}** es *train* (se aprende de ahí); desde esa fecha es *test*
  (se usa solo para evaluar). Así se mide si el modelo acierta con lo que pasó **después**.
- **Universo:** proveedores con al menos **{mp}** entidades distintas y entidades con al menos **{me}** proveedores
  distintos en train. Con menos datos no se puede recomendar ni evaluar.
""".format(corte=r["parametros"]["fecha_corte"], mp=r["parametros"]["min_entidades_por_proveedor"], me=r["parametros"]["min_proveedores_por_entidad"]))

tab_emb, tab_uni, tab_part = st.tabs(["Qué datos se pierden", "El universo", "Particiones en Spark"])

with tab_emb:
    st.subheader("De las adjudicaciones a los proveedores identificables")
    df = pd.DataFrame({
        "grupo": ["Adjudicaciones en total", "Sin RUC", "Consorcios (RUC de 7 dígitos)", "Usables (RUC real)"],
        "adjudicaciones": [emb["adjudicaciones_total"], emb["sin_ruc"], emb["consorcio_7_digitos"], emb["usables_con_ruc_real"]],
    })
    df["porcentaje"] = (100 * df.adjudicaciones / emb["adjudicaciones_total"]).round(1)
    fig = px.bar(df, x="adjudicaciones", y="grupo", orientation="h", text="porcentaje",
                 labels={"adjudicaciones": "Adjudicaciones", "grupo": ""})
    fig.update_traces(texttemplate="%{text}%", textposition="outside")
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"""
- **Qué es un consorcio aquí:** una asociación temporal que firma con un RUC de **7 dígitos** distinto en cada proceso.
  No se puede seguir en el tiempo, así que **no se une por nombre** (se arriesgaría mezclar empresas distintas): se deja fuera y se declara.
- **Proveedores con RUC real:** {r['proveedores_con_ruc_real']:,}. De ellos, **{r['ruc_con_varios_nombres']}** aparecen escritos con más de un nombre;
  se conserva el nombre más frecuente. El RUC de 11 dígitos es estable, por eso no hizo falta comparar textos (MinHash/LSH).
- **Participaciones (postores):** {r['postores_filas']:,} filas, de las cuales {r['postores_consorcio_filas']:,} son consorcios.
""")

with tab_uni:
    st.subheader("Tamaño de la matriz")
    c = st.columns(4)
    c[0].metric("Proveedores", f"{uni['proveedores']:,}")
    c[1].metric("Entidades", f"{uni['entidades']:,}")
    c[2].metric("Pares en train", f"{uni['pares_train']:,}", help="Un par es una entidad que le adjudicó al menos una vez a un proveedor, antes del corte.")
    c[3].metric("Pares en test", f"{uni['pares_test']:,}", help="Lo mismo, desde el corte.")
    st.markdown(f"""
- **Densidad {uni['densidad_pct']:.2f}%:** de cada 1,000 posibles combinaciones entidad–proveedor, solo ~2 existen. Por eso recomendar es difícil.
- **Pares nuevos en test:** {uni['pares_test_nuevos']:,}, en {uni['entidades_con_par_nuevo']:,} entidades. Son contrataciones que la entidad **no tenía** en train: lo que un recomendador debe "descubrir".
- El test tiene solo el **{r['pct_adjudicaciones_test']:.0f}%** de las adjudicaciones: son pocos meses, así que las métricas pueden cambiar con más datos.
- Nota: los dos filtros se aplican a la vez, y 8 proveedores y 23 entidades quedan sin ningún par en train. Por eso en la evaluación hay 4,926 pares nuevos y no 4,929.
""")

with tab_part:
    st.subheader("Cuántas particiones usar en una agregación")
    t = pd.DataFrame(r["particionamiento"]["tiempos"])
    fig = px.line(t, x="particiones_shuffle", y="segundos", markers=True, log_x=True,
                  labels={"particiones_shuffle": "Particiones del shuffle (escala log)", "segundos": "Segundos"})
    st.plotly_chart(fig, width="stretch")
    st.markdown("""
Una **partición** es un pedazo de los datos que Spark procesa por separado. Con un conjunto pequeño (decenas de miles de pares),
**más particiones no ayuda: cuesta más repartirlas que calcularlas**. Los valores por defecto de Spark (200) fueron ~7 veces más lentos que 1 a 8 particiones.
Los tiempos dependen de la máquina; solo importa la forma de la curva.
""")
    with st.expander("Plan de ejecución de la agregación"):
        st.code(r["particionamiento"]["plan"], language="text")

st.caption("Notebook: `P2_01_Base_Relacional`. Todo se calculó antes; esta página solo lee los resultados.")
siguiente("pages/12_Grafo.py", "Grafo de co-participación")
