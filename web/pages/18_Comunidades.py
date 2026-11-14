import pandas as pd
import plotly.express as px
import streamlit as st

from utils import encabezado, siguiente
from utils_p2 import csv_p2, json_p2

st.title("Proyecto 2 · Parte V · Comunidades")

res = json_p2("p5_resumen.json")
lou = res["louvain_completo_resolucion_1"]
sub, bc = res["subgrafo"], res["bigclam"]
por_res = csv_p2("com_resolucion.csv")

encabezado(
    "¿Los proveedores forman grupos que se encuentran en los mismos procesos, y qué métodos permiten verlos?",
    f"Sí. Louvain sobre el grafo completo ({res['grafo']['nodos']:,} proveedores) encuentra {int(lou['comunidades'])} comunidades con modularidad Q = {lou['Q']:.2f} "
    f"(0 sería el azar). Girvan–Newman y el espectral solo se pueden correr sobre una muestra. Cada comunidad es una agrupación para revisar con más contexto, no una acusación.",
)

st.markdown("""
**Qué es una comunidad:** un grupo de proveedores que coinciden mucho entre sí en los mismos procesos y menos con el resto.
**Modularidad Q:** compara las conexiones dentro de los grupos con las que habría si las conexiones fueran al azar. **Q cerca de 0 = no mejor que el azar; Q más alta = grupos más cerrados.**
""")

tab_met, tab_esc, tab_lou, tab_sol = st.tabs(["Métodos y Q", "Por qué hace falta una muestra", "Comunidades del grafo completo (resolución ajustable)", "Comunidades solapadas"])

with tab_met:
    st.markdown(f"""
Los cuatro métodos de clase se compararon sobre **la misma muestra**: {sub['nodos']} proveedores elegidos al azar entre los que tienen al menos 50 participaciones
({sub['aristas']} conexiones, densidad {sub['densidad']}). Se usa la red **sin pesos** para todos.
""")
    met = csv_p2("com_metodos.csv").rename(columns={"metodo": "Método", "necesita_k": "¿Necesita el número de grupos?", "comunidades": "Comunidades", "Q": "Q", "segundos": "Segundos", "escala": "¿Escala a 40 mil nodos?"})
    met["Segundos"] = met["Segundos"].apply(lambda x: "—" if pd.isna(x) else f"{x:g}")
    st.dataframe(met, width="stretch", hide_index=True)
    a, b = st.columns(2)
    gn = csv_p2("com_gn_curva.csv"); esp = csv_p2("com_espectral.csv")
    df = pd.concat([gn.assign(Método="Girvan–Newman"), esp.assign(Método="Espectral")])
    fig = px.line(df, x="k", y="Q", color="Método", markers=True, labels={"k": "Número de comunidades", "Q": "Modularidad Q"})
    a.plotly_chart(fig, width="stretch")
    sem = csv_p2("com_semillas.csv")
    fig2 = px.strip(sem, x="metodo", y="Q", color="metodo", labels={"metodo": "Método (10 semillas)", "Q": "Modularidad Q"})
    fig2.update_layout(showlegend=False)
    b.plotly_chart(fig2, width="stretch")
    st.markdown("""
**Cómo leerlo.**
- **Izquierda:** Girvan–Newman y el espectral eligen el número de comunidades donde Q es más alta.
- **Derecha:** LPA da resultados **distintos según la semilla**; Louvain casi no cambia.
- **Louvain** logra la Q más alta y es rápido. **LPA** sirve como primer paso rápido.
- Todos los métodos dan una Q **mucho mayor que 0**: los grupos son reales, no azar.
""")

with tab_esc:
    esc = csv_p2("com_escala.csv")
    st.dataframe(esc.rename(columns={"nodos": "Nodos", "aristas": "Aristas", "seg_un_betweenness": "Segundos de un edge betweenness", "seg_gn_hasta_10": "Segundos de Girvan–Newman (hasta 10 comunidades)"}),
                 width="stretch", hide_index=True)
    fig = px.line(esc, x="nodos", y="seg_gn_hasta_10", markers=True, labels={"nodos": "Nodos de la muestra", "seg_gn_hasta_10": "Segundos de Girvan–Newman"})
    st.plotly_chart(fig, width="stretch")
    st.markdown(f"""
**Por qué los métodos exactos exigen una muestra**
- **Girvan–Newman** recalcula el *edge betweenness* de **todas** las aristas cada vez que quita una. Cada cálculo cuesta del orden de *n × m*; el tiempo crece mucho más rápido que el tamaño. Con {res['grafo']['nodos']:,} nodos y {res['grafo']['aristas']:,} aristas, un solo cálculo tardaría unas {res['escala']['horas_estimadas_un_betweenness_grafo_completo']:.0f} horas (estimación).
- **Espectral** necesita los vectores propios de una matriz de *n × n* (unos 1,600 millones de celdas aquí).
- **Lo que sí escala:** **LPA** (recorre las aristas una vez por vuelta) y **Louvain** (mueve nodos y agrupa comunidades). Louvain procesó las {res['grafo']['aristas']:,} aristas en {lou['segundos']:.0f} segundos.
- **Costo de la muestra:** conserva solo una parte de las aristas; sirve para **comparar métodos**, no para describir el mercado.
""")

with tab_lou:
    resoluciones = sorted(por_res.resolucion.unique())
    r = st.select_slider("Resolución de Louvain", options=resoluciones, value=1.0,
                         help="Mayor resolución = comunidades más pequeñas y más numerosas. 1.0 es el Louvain estándar de clase.")
    f = por_res[por_res.resolucion == r].iloc[0]
    m = st.columns(5)
    m[0].metric("Comunidades en total", f"{int(f.comunidades):,}", help="Incluye unas 100 islas diminutas (menos de 10 proveedores) que no se conectan con el bloque principal.")
    m[1].metric("Comunidades de 10 o más", f"{int(f.comunidades_de_10_o_mas):,}")
    m[2].metric("Modularidad Q", f"{f.Q:.3f}")
    m[3].metric("Comunidad más grande", f"{int(f.mayor):,} proveedores")
    m[4].metric("En las 10 mayores", f"{f.pct_en_las_10_mayores:.1f}%", help="Qué parte de los proveedores está en las 10 comunidades más grandes.")
    perfil = csv_p2("com_perfil.csv")
    p = perfil[perfil.resolucion == r].copy()
    p["etiqueta"] = "Comunidad " + p.comunidad.astype(str)
    fig = px.bar(p, x="etiqueta", y="proveedores", color="cohesion", color_continuous_scale="Blues", hover_data=["departamento_principal", "pct_departamento", "categoria_principal", "pct_categoria"],
                 labels={"etiqueta": "", "proveedores": "Proveedores", "cohesion": "Cohesión"})
    st.plotly_chart(fig, width="stretch")
    st.dataframe(p[["comunidad", "proveedores", "cohesion", "departamento_principal", "pct_departamento", "categoria_principal", "pct_categoria", "participaciones_medianas", "lideres"]].rename(columns={
        "comunidad": "Comunidad", "proveedores": "Proveedores", "cohesion": "Cohesión", "departamento_principal": "Departamento principal", "pct_departamento": "% en ese departamento",
        "categoria_principal": "Categoría principal", "pct_categoria": "% en esa categoría", "participaciones_medianas": "Procesos típicos por proveedor", "lideres": "Los 3 más conectados"}),
        width="stretch", hide_index=True)
    st.markdown("""
**Cómo leer la tabla**
- **Cohesión:** de todas las conexiones de los miembros, qué parte queda **dentro** de la comunidad (1 = cerrada; cerca de 0 = sus miembros se conectan sobre todo con otros grupos).
- **Departamento y categoría principal:** dónde y en qué rubro (`goods` bienes, `services` servicios, `works` obras) ofertan sus miembros con más frecuencia, y qué porcentaje representa.
- Las comunidades grandes se separan sobre todo por **rubro**: la categoría principal reúne la mayor parte de sus miembros. La **región pesa menos** (Lima domina en muchas porque concentra procesos). Proveedores del mismo rubro se encuentran en los mismos procesos sin que haya nada raro.
- Una comunidad es una **agrupación a revisar con más contexto** (quién compra, qué compra, en qué fechas), **nunca una prueba de acuerdos**. Los RUC que no empiezan con 20 están enmascarados.
""")
    st.caption("Con resolución mayor aparecen más comunidades relevantes y más chicas. La Q es máxima cerca de resolución 1, que es lo que optimiza Louvain. No hay una resolución correcta: depende de qué tan fino se quiera ver.")

with tab_sol:
    st.markdown(f"""
En una partición cada proveedor está en **una** comunidad. Un proveedor real puede estar en **varios mercados**. **BigCLAM** (modelo de afiliación a comunidades) da a cada proveedor una
«fuerza de pertenencia» por comunidad; pertenece a las que superan un umbral. Se calculó solo sobre la muestra de {sub['nodos']} proveedores.
""")
    m = st.columns(4)
    m[0].metric("Comunidades (≥ 3 nodos)", bc["comunidades_con_3_o_mas"])
    m[1].metric("Proveedores en 2 o más", f"{bc['nodos_solapados']} ({bc['pct_solapados']}%)")
    m[2].metric("Coincidencia con Louvain (ARI)", f"{bc['ari_vs_louvain']:.2f}", help="1 = mismas comunidades; 0 = como el azar. Se compara la comunidad dominante de cada proveedor.")
    m[3].metric("Umbral de pertenencia", f"{bc['umbral_delta']:.2f}")
    d = pd.DataFrame({"Zona": ["Entre proveedores solapados", "Dentro de las comunidades (promedio)", "Toda la muestra"],
                      "Densidad de conexiones": [bc["densidad_solapados"], bc["densidad_media_comunidades"], bc["densidad_subgrafo"]]})
    st.plotly_chart(px.bar(d, x="Zona", y="Densidad de conexiones"), width="stretch")
    a, b = st.columns(2)
    a.markdown("**Efecto del número de comunidades C**")
    a.dataframe(csv_p2("com_bigclam_C.csv").rename(columns={"C": "C", "log_verosimilitud": "Log-verosimilitud", "comunidades_con_3_o_mas": "Comunidades (≥ 3)", "nodos_en_2_o_mas": "Proveedores en 2 o más",
                                                           "pct_solapados": "% solapados", "nodos_sin_comunidad": "Sin comunidad"}), width="stretch", hide_index=True)
    b.markdown("**Proveedores en más comunidades**")
    b.dataframe(csv_p2("com_solapados.csv").rename(columns={"nombre": "Proveedor", "ruc": "RUC", "comunidades": "Comunidades", "grado": "Conexiones", "departamento": "Departamento", "categoria": "Categoría"}),
                width="stretch", hide_index=True)
    st.markdown("""
**Cómo leerlo.** En clase se vio que la densidad en las zonas de solapamiento es mayor que dentro de cada comunidad. **Aquí no se cumple**: los proveedores solapados están mucho más conectados entre sí que el promedio de la muestra, pero **menos** que dentro de las comunidades. Con solo unos 20 proveedores solapados y una red dispersa, el resultado es poco concluyente. Los proveedores «sin comunidad» son los de pocas conexiones en la muestra.
Estar en varias comunidades **no tiene nada de raro**: un proveedor puede vender en varias regiones o rubros. La implementación es simple (NumPy, 270 nodos); escalarla exigiría la versión por bloques del método original.
""")

st.warning("Una comunidad es una **agrupación para revisar**, no una acusación. Proveedores del mismo rubro y de la misma región se encuentran en los mismos procesos de forma natural. Antes de concluir algo habría que mirar quién compra, qué compra y en qué fechas.")

st.caption("Notebook: `P2_08_Comunidades` (local: NetworkX, NumPy, scikit-learn; Spark solo para el perfil de las comunidades). BigCLAM es un método extra que la clase solo menciona.")
siguiente("pages/19_Embeddings.py", "Embeddings de nodos")
