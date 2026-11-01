import pandas as pd
import plotly.express as px
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Grafo de co-participación")

res = json_p2("grafo_resumen.json")
umb = csv_p2("grafo_umbrales.csv")
g = res["grafo_final"]

encabezado(
    "¿Qué proveedores se encuentran con frecuencia en los mismos procesos, y esa red separa mercados?",
    f"Con 2 procesos en común o más, el grafo tiene {g['nodos']:,} proveedores y {g['aristas']:,} conexiones, "
    f"y {g['pct_mayor_componente']}% está en un solo bloque conectado. La red por sí sola no separa mercados; eso se intenta con comunidades (Partes IV–VI, siguiente etapa).",
)

st.markdown(f"""
### Qué es este grafo
- **Nodo:** un proveedor que se presentó a al menos **{res['parametros']['min_participaciones']}** procesos.
- **Arista:** dos proveedores que ofertaron en el mismo proceso. **Peso = en cuántos procesos coincidieron.**
- **Tope de postores ({res['parametros']['tope_postores']}):** los procesos con más postores que el tope no generan aristas, porque un proceso con 100 postores crearía 4,950 pares y llenaría la red de coincidencias casuales.
- **Peso mínimo:** coincidir una sola vez puede ser azar. El control de abajo muestra qué pasa al exigir más coincidencias.
""")

tab_umbral, tab_grado, tab_top, tab_tope = st.tabs(["Peso mínimo", "Distribución de conexiones", "Más conectados", "Tope de postores"])

with tab_umbral:
    peso = st.slider("Peso mínimo (procesos en común para dibujar una arista)", int(umb.peso_minimo.min()), int(umb.peso_minimo.max()), 2)
    fila = umb[umb.peso_minimo == peso].iloc[0]
    c = st.columns(4)
    c[0].metric("Proveedores (nodos)", f"{int(fila.nodos):,}", help="Proveedores con al menos una conexión de ese peso.")
    c[1].metric("Conexiones (aristas)", f"{int(fila.aristas):,}")
    c[2].metric("Bloques conectados", f"{int(fila.componentes):,}", help="Un bloque (componente) es un grupo de proveedores unidos entre sí por alguna cadena de conexiones.")
    c[3].metric("Bloque más grande", f"{fila.pct_mayor_componente:.1f}%", help="Porcentaje de los proveedores que está en el bloque más grande.")
    st.caption(f"Conexiones por proveedor (grado): promedio {fila.grado_medio:.1f}, mediana {fila.grado_mediano:.0f}, máximo {int(fila.grado_max):,}.")
    a, b = st.columns(2)
    f1 = px.line(umb, x="peso_minimo", y="aristas", markers=True, log_y=True, labels={"peso_minimo": "Peso mínimo", "aristas": "Aristas (escala log)"})
    f1.add_vline(x=peso, line_dash="dash")
    a.plotly_chart(f1, width="stretch")
    f2 = px.line(umb, x="peso_minimo", y="pct_mayor_componente", markers=True, labels={"peso_minimo": "Peso mínimo", "pct_mayor_componente": "% en el bloque más grande"})
    f2.update_yaxes(range=[90, 100]); f2.add_vline(x=peso, line_dash="dash")
    b.plotly_chart(f2, width="stretch")
    st.markdown("""
**Cómo leerlo:** al exigir más coincidencias las conexiones caen muy rápido (la mayoría de los pares coincidió una sola vez),
pero el bloque más grande sigue reuniendo a casi todos los proveedores. La red es **un bloque grande, no islas**: los mercados, si existen, están dentro de él.
""")

with tab_grado:
    d = csv_p2("grafo_grado.csv")
    d["rango"] = [f"{int(a)}" if a == b else f"{int(a)}–{int(b)}" if b < 1e9 else f"{int(a)}+" for a, b in zip(d.grado_desde, d.grado_hasta)]
    fig = px.bar(d, x="rango", y="n_nodos", labels={"rango": "Conexiones del proveedor (grado)", "n_nodos": "Proveedores"})
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"Muchos proveedores tienen pocas conexiones y unos pocos tienen miles (máximo {g['grado_max']:,}). El promedio ({g['grado_medio']}) es muy superior a la mediana ({g['grado_mediano']:.0f}) por esa cola larga.")

with tab_top:
    top = pd.DataFrame(res["top_conectados"]).rename(columns={"nombre": "Proveedor", "ruc": "RUC", "grado": "Conexiones", "peso_total": "Suma de procesos en común"})
    st.dataframe(top, width="stretch", hide_index=True)
    st.markdown("Tener muchas conexiones **no prueba nada**: solo significa que ofertan en muchísimos procesos. Se usan como punto de partida para PageRank y comunidades. Los RUC que no empiezan con 20 se muestran enmascarados.")

with tab_tope:
    t = pd.DataFrame(res["tabla_tope"]).rename(columns={"tope": "Tope de postores", "procesos": "Procesos que sí generan aristas", "pares_posibles": "Pares posibles", "pct_procesos": "% de los procesos"})
    t["Tope de postores"] = t["Tope de postores"].astype(str)
    st.dataframe(t, width="stretch", hide_index=True)
    st.markdown(f"Con tope {res['parametros']['tope_postores']} se mantiene el 90.8% de los procesos y se evitan unos 20.7 millones de pares (10.7 millones frente a 31.4 millones sin tope), que en su mayoría serían coincidencias casuales de procesos masivos.")

st.caption("Notebook: `P2_02_Grafo_Coparticipacion` (Spark: auto-unión de postores por proceso).")
siguiente("pages/13_Clustering.py", "Clustering")
